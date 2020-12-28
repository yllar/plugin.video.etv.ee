# -*- coding: utf-8 -*-
import json
import locale
import os
import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from datetime import datetime, timedelta

from resources.lib.downloader import download_url as download_url
from resources.lib.err import *
import inputstreamhelper
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    locale.setlocale(locale.LC_ALL, 'et_EE.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')

__settings__ = xbmcaddon.Addon(id='plugin.video.etv.ee')

DAYS = int(__settings__.getSetting('days'))
if DAYS < 1:
    DAYS = 1

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
DRM = 'com.widevine.alpha'
is_helper = inputstreamhelper.Helper('mpd', drm=DRM)


class EtvException(Exception):
    pass


class Etv(object):
    def list_channels(self):
        items = list()
        item = xbmcgui.ListItem('ETV')
        item.setArt({'fanart': FANART, 'poster': LOGOETV, 'icon': LOGOETV})
        items.append((PATH + '?action=enter&channel=%s' % 'etv', item, True))

        item = xbmcgui.ListItem('ETV2')
        item.setArt({'fanart': FANART2, 'poster': LOGOETV2, 'icon': LOGOETV2})
        items.append((PATH + '?action=enter&channel=%s' % 'etv2', item, True))

        item = xbmcgui.ListItem('ETV+')
        item.setArt({'fanart': FANART3, 'poster': LOGOETVPLUSS, 'icon': LOGOETVPLUSS})
        items.append((PATH + '?action=enter&channel=%s' % 'etvpluss', item, True))

        item = xbmcgui.ListItem('ETV otse')
        item.setArt({'fanart': FANART, 'poster': LOGOETV, 'icon': LOGOETV})
        item.setInfo('video', infoLabels={"Title": "ETV otse"})
        item.setProperty('IsPlayable', 'true')
        items.append(('http://sb.err.ee/live/etv.m3u8?short=true', item))

        item = xbmcgui.ListItem('ETV2 otse')
        item.setArt({'fanart': FANART2, 'poster': LOGOETV2, 'icon': LOGOETV2})
        item.setInfo('video', infoLabels={"Title": "ETV2 otse"})
        item.setProperty('IsPlayable', 'true')
        items.append(('http://sb.err.ee/live/etv2.m3u8?short=true', item))

        item = xbmcgui.ListItem('ETV+ otse')
        item.setArt({'fanart': FANART3, 'poster': LOGOETVPLUSS, 'icon': LOGOETVPLUSS})
        item.setInfo('video', infoLabels={"Title": "ETV+ otse"})
        item.setProperty('IsPlayable', 'true')
        items.append(('http://sb.err.ee/live/etvpluss.m3u8?short=true', item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def list_dates(self, channel):
        items = list()

        tana = "%s %s" % (ADDON.getLocalizedString(30003), datetime.now().strftime('%Y-%m-%d'))
        tanad = datetime.now().strftime('%Y-%m-%d')
        item = xbmcgui.ListItem(tana)
        item.setArt({'fanart': FANART, 'poster': FANART, 'icon': FANART})
        items.append((PATH + '?action=list&channel=%s&date=%s' % (channel, tanad), item, True))

        for paevad in range(1, DAYS):
            paev = datetime.now() - timedelta(days=paevad)
            paevd = paev.strftime('%A %Y-%m-%d')
            paev = paev.strftime('%Y-%m-%d')
            item = xbmcgui.ListItem(paevd)
            item.setArt({'fanart': FANART, 'poster': FANART, 'icon': FANART})
            items.append((PATH + '?action=list&channel=%s&date=%s' % (channel, paev), item, True))
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def list_schedule(self, channel, date):
        year, month, day = date.split("-")
        url = 'https://etv.err.ee/api/tvSchedule/getTimelineSchedule2?year=%s&month=%s&day=%s&channel=%s' % (
            year, month, day, channel)
        html = download_url(url)
        if not html:
            raise EtvException(ADDON.getLocalizedString(203))

        html = json.loads(html)
        items = list()
        for s in html:
            try:
                if s['contents'][0]["medias"]:
                    if s["contents"][0]["horizontalPhotos"][0]["photoTypes"]["26"]["url"]:
                        fanart = s["contents"][0]["horizontalPhotos"][0]["photoTypes"]["26"]["url"]
                    else:
                        fanart = FANART
                    title = s['name']
                    plot = s['extension']
                    year = s['progProdYear']

                    infoLabels = {
                        'plot': plot,
                        'title': title,
                        'year': year
                    }

                    item = xbmcgui.ListItem(title)
                    item.setInfo('video', infoLabels)
                    item.setProperty('IsPlayable', 'true')
                    item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                    items.append((PATH + '?action=watch&vaata=%s' % s['contentId'], item))
            except IndexError:
                pass
        xbmc.executebuiltin("Container.SetViewMode(500)")
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def get_media_data(self, key):
        url = "http://etv.err.ee/services/api/media/mediaData?stream=%s" % key
        data = download_url(url)
        if data:
            json_data = json.loads(data)
            return json_data['media']['src']['hls']

    def get_media_location(self, key):
        url = "https://etv.err.ee/api/tv/getTvPageData?contentId=%s&contentOnly=true" % key
        token = ""
        license_server = ""
        html = download_url(url)
        if html:
            html = json.loads(html)
            url = html['showInfo']['media']['src']['hls']
            drm = html['pageControlData']['mainContent']['medias'][0]['restrictions']['drm']
            if drm:
                token = html['pageControlData']['mainContent']['medias'][0]['jwt']
                license_server = html['pageControlData']['mainContent']['medias'][0]['licenseServerUrl']['widevine']
                url = html['pageControlData']['mainContent']['medias'][0]['src']['dash']
            sub = []
            languages = []
            languages.extend((
                get_subtitle_language(__settings__.getSetting('primaryLanguage')),
                get_subtitle_language(__settings__.getSetting('secondaryLanguage'))
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

            return url.replace('//', 'https://', 1), sub, token, license_server
        else:
            raise EtvException(ADDON.getLocalizedString(202))

    def play_stream(self, vaata):
        if vaata == '00000000-0000-0000-0000-000000000000':
            raise EtvException(ADDON.getLocalizedString(202))
        if "live/" in vaata:
            saade = vaata
        else:
            saade, subs, token, license_server = EtvAddon.get_media_location(vaata)
        xbmc.log('saade: %s' % saade, xbmc.LOGNOTICE)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        item = xbmcgui.ListItem(saade, path=saade)
        if token:
            if is_helper.check_inputstream():
                item.setContentLookup(False)
                item.setMimeType('application/dash+xml')
                if KODI_VERSION_MAJOR >= 19:
                    item.setProperty('inputstream', is_helper.inputstream_addon)
                else:
                    item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                    item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                    item.setProperty('inputstream.adaptive.license_type', DRM)
                    item.setProperty('inputstream.adaptive.license_key',
                                     license_server + '|X-AxDRM-Message=' + token + '|R{SSM}|')
        try:
            if subs:
                item.setSubtitles(subs)
        except:
            pass
        playlist.add(saade, item)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def display_error(self, message='n/a'):
        heading = ''
        line1 = ADDON.getLocalizedString(200)
        line2 = ADDON.getLocalizedString(201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = dict(parse_qsl(sys.argv[2][1:]))

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv.jpg')
    FANART2 = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv2.jpg')
    FANART3 = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv+.jpg')
    LOGOETV = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv-logo.png')
    LOGOETV2 = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv2-logo.png')
    LOGOETVPLUSS = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'etv+-logo.png')


    EtvAddon = Etv()
    if PARAMS:
        if PARAMS['action'] == 'enter':
            EtvAddon.list_dates(PARAMS['channel'])
        elif PARAMS['action'] == 'watch':
            EtvAddon.play_stream(PARAMS['vaata'])
        else:
            EtvAddon.list_schedule(PARAMS['channel'], PARAMS['date'])
    else:
        EtvAddon.list_channels()
