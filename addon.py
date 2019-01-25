#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#      Copyright (C) 2016 Yllar Pajus
#      https://pilves.eu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
from datetime import datetime, timedelta
import locale
import os
import sys
import urlparse
import urllib2
import json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

try:
    locale.setlocale(locale.LC_ALL, 'et_EE.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')

__settings__ = xbmcaddon.Addon(id='plugin.video.etv.ee')

DAYS = int(__settings__.getSetting('days'))
if DAYS < 1:
    DAYS = 1


class Logger:
    def write(data):
        xbmc.log(data)

    write = staticmethod(write)


sys.stdout = Logger
sys.stderr = Logger


class EtvException(Exception):
    pass


class Etv(object):
    def download_url(self, url):
        for retries in range(0, 5):
            try:
                r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
                r.add_header('User-Agent',
                             'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
                u = urllib2.urlopen(r, timeout=30)
                contents = u.read()
                u.close()
                return contents
            except Exception, ex:
                if retries > 5:
                    raise EtvException(ex)

    def list_channels(self):
        items = list()
        item = xbmcgui.ListItem('ETV', iconImage=LOGOETV)
        item.setProperty('Fanart_Image', FANART)
        items.append((PATH + '?channel=%s' % 'etv', item, True))
        item = xbmcgui.ListItem('ETV2', iconImage=LOGOETV2)
        item.setProperty('Fanart_Image', FANART2)
        items.append((PATH + '?channel=%s' % 'etv2', item, True))
        item = xbmcgui.ListItem('ETV+', iconImage=LOGOETVPLUSS)
        item.setProperty('Fanart_Image', FANART3)
        items.append((PATH + '?channel=%s' % 'etvpluss', item, True))

        item = xbmcgui.ListItem('ETV otse', iconImage=LOGOETV)
        item.setProperty('Fanart_Image', FANART)
        item.setInfo('video', infoLabels={"Title": "ETV otse"})
        item.setProperty('IsPlayable', 'true')
        # items.append(('http://err1.babahhcdn.com/live/etv.m3u8', item))
        items.append(('https://err10.babahhcdn.com/live/etv.m3u8', item))

        item = xbmcgui.ListItem('ETV2 otse', iconImage=LOGOETV2)
        item.setProperty('Fanart_Image', FANART2)
        item.setInfo('video', infoLabels={"Title": "ETV2 otse"})
        item.setProperty('IsPlayable', 'true')
        items.append(('http://err1.babahhcdn.com/live/etv2.m3u8', item))

        item = xbmcgui.ListItem('ETV+ otse', iconImage=LOGOETVPLUSS)
        item.setProperty('Fanart_Image', FANART3)
        item.setInfo('video', infoLabels={"Title": "ETV+ otse"})
        item.setProperty('IsPlayable', 'true')
        items.append(('http://err1.babahhcdn.com/live/etvpluss.m3u8', item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def list_dates(self, channel):
        items = list()

        tana = "%s %s" % (ADDON.getLocalizedString(30003), datetime.now().strftime('%Y-%m-%d'))
        tanad = datetime.now().strftime('%Y-%m-%d')
        item = xbmcgui.ListItem(tana, iconImage=FANART)
        item.setProperty('Fanart_Image', FANART)
        items.append((PATH + '?channel=%s&date=%s' % (channel, tanad), item, True))

        for paevad in range(1, DAYS):
            paev = datetime.now() - timedelta(days=paevad)
            paevd = paev.strftime('%A %Y-%m-%d')
            paev = paev.strftime('%Y-%m-%d')
            item = xbmcgui.ListItem(paevd, iconImage=FANART)
            item.setProperty('Fanart_Image', FANART)
            items.append((PATH + '?channel=%s&date=%s' % (channel, paev), item, True))
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def list_schedule(self, channel, date):
        year, month, day = date.split("-")
        url = 'https://etv.err.ee/api/tvSchedule/getTimelineSchedule2?year=%s&month=%s&day=%s&channel=%s' % (
            year, month, day, channel)
        buggalo.addExtraData('url', url)
        html = self.download_url(url)
        if not html:
            raise EtvException(ADDON.getLocalizedString(203))

        html = json.loads(html)
        items = list()
        for s in html:
            if s['mediaExist']:
                if s['horizontalPhotoUrl']:
                    fanart = s['horizontalPhotoUrl']
                else:
                    fanart = FANART
                title = s['programName']
                plot = s['name']

                infoLabels = {
                    'plot': plot,
                    'title': title
                }

                item = xbmcgui.ListItem(title, iconImage=fanart)
                item.setInfo('video', infoLabels)
                item.setProperty('IsPlayable', 'true')
                item.setProperty('Fanart_Image', fanart)
                items.append((PATH + '?vaata=%s' % s['contentId'], item))
        xbmc.executebuiltin("Container.SetViewMode(500)")
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def get_media_data(self, key):
        url = "http://etv.err.ee/services/api/media/mediaData?stream=%s" % key
        buggalo.addExtraData('url', url)
        data = self.download_url(url)
        if data:
            json_data = json.loads(data)
            return json_data['media']['src']['hls']

    def get_media_location(self, key):
        url = "https://etv.err.ee/api/tv/getTvPageData?contentId=%s&contentOnly=true" % key
        buggalo.addExtraData('url', url)
        html = self.download_url(url)
        if html:
            html = json.loads(html)
            url = html['showInfo']['media']['src']['hls']

            sub = []
            languages = []
            languages.extend((
                self.get_subtitle_language(__settings__.getSetting('primaryLanguage')),
                self.get_subtitle_language(__settings__.getSetting('secondaryLanguage'))
            ))

            try:
                for language in languages:
                    for subtitle in html['showInfo']['media']['subtitles']:
                        if subtitle['srclang'] == language:
                            xbmc.log('subtitle path: %s' % (subtitle['src']), xbmc.LOGNOTICE)
                            sub = (subtitle['src'], language)
                            break
            except:
                pass
            
            return url.replace('//', 'https://'), sub
        else:
            raise EtvException(ADDON.getLocalizedString(202))

    def get_subtitle_language(self, lang):
        # helper function to map human readable settings to required abbreviation
        if int(lang) == 0:
            return "ET"
        elif int(lang) == 1:
            return "VA"
        elif int(lang) == 2:
            return "RU"
        else:
            pass

    def play_stream(self, vaata):
        if vaata == '00000000-0000-0000-0000-000000000000':
            raise EtvException(ADDON.getLocalizedString(202))
        if "live/" in vaata:
            saade = vaata
        else:
            saade, subs = EtvAddon.get_media_location(vaata)
        buggalo.addExtraData('saade', saade)
        xbmc.log('saade: %s' % saade, xbmc.LOGNOTICE)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        item = xbmcgui.ListItem(saade, iconImage=ICON, path=saade)

        try:
            if subs:
                item.setSubtitles(subs)
        except:
            pass
        playlist.add(saade, item)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def display_error(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(200)
        line2 = ADDON.getLocalizedString(201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'etv.jpg')
    FANART2 = os.path.join(ADDON.getAddonInfo('path'), 'etv2.jpg')
    FANART3 = os.path.join(ADDON.getAddonInfo('path'), 'etv+.jpg')
    LOGOETV = os.path.join(ADDON.getAddonInfo('path'), 'etv-logo.png')
    LOGOETV2 = os.path.join(ADDON.getAddonInfo('path'), 'etv2-logo.png')
    LOGOETVPLUSS = os.path.join(ADDON.getAddonInfo('path'), 'etv+-logo.png')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    buggalo.SUBMIT_URL = 'https://pilves.eu/exception/submit.php'

    EtvAddon = Etv()
    try:
        if PARAMS.has_key('channel') and PARAMS.has_key('date'):
            EtvAddon.list_schedule(PARAMS['channel'][0], PARAMS['date'][0])
        elif PARAMS.has_key('channel'):
            EtvAddon.list_dates(PARAMS['channel'][0])
        elif PARAMS.has_key('vaata'):
            EtvAddon.play_stream(PARAMS['vaata'][0])
        else:
            EtvAddon.list_channels()
    except EtvException, ex:
        EtvAddon.display_error(str(ex))
    except Exception:
        buggalo.onExceptionRaised()
