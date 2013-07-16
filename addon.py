#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#      Copyright (C) 2012 Yllar Pajus
#      http://loru.mine.nu
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
import re

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

try:
  locale.setlocale(locale.LC_ALL, 'et_EE.UTF-8')
except locale.Error:
  locale.setlocale(locale.LC_ALL, 'C')

__settings__  = xbmcaddon.Addon(id='plugin.video.etv.ee')

DAYS = int(__settings__.getSetting('days'))
if DAYS < 1:
  DAYS = 1

class EtvException(Exception):
  pass

class Etv(object):
  def downloadUrl(self,url):
    for retries in range(0, 5):
      try:
	r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
	r.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
	u = urllib2.urlopen(r, timeout = 30)
	contents = u.read()
	u.close()
	return contents
      except Exception, ex:
        if retries > 5:
	  raise EtvException(ex)
	
  def listChannels(self):
    items = list()
    item = xbmcgui.ListItem('etv', iconImage=FANART)
    item.setProperty('Fanart_Image', FANART)
    items.append((PATH + '?channel=%s' % 'etv', item, True))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)

    
  def listDates(self,channel):
    items = list()

    tana = "%s %s" % (ADDON.getLocalizedString(30003), datetime.now().strftime('%Y-%m-%d'))
    tanad = datetime.now().strftime('%Y-%m-%d')
    item = xbmcgui.ListItem(tana, iconImage=FANART)
    item.setProperty('Fanart_Image', FANART)
    items.append((PATH + '?channel=%s&date=%s' % (channel,tanad), item, True))
    
    for paevad in range(1,DAYS):
      paev = datetime.now() - timedelta(days=paevad)
      paevd =  paev.strftime('%A %Y-%m-%d')
      paev = paev.strftime('%Y-%m-%d')
      item = xbmcgui.ListItem(paevd, iconImage=FANART)
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?channel=%s&date=%s' % (channel,paev), item, True))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)
  
  def listSchedule(self,channel,date):
    url = 'http://%s.err.ee/arhiiv.php?sort=paev&paev=%s' % (channel,date)
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if not html:
      raise EtvException(ADDON.getLocalizedString(203))
    
    items = list()
    html = html.replace('<br />', '\n')
    for s in re.finditer('.*href="arhiiv.php\?id=([^"]+).*"><b>([^<]+).*\(([^)]+)\).*</div>',html):
      #print s.group(1), s.group(2), s.group(3)
      title = s.group(2)
      date = s.group(3)
      
      infoLabels = {
	'date' : date,
	'title' : title
      }

      item = xbmcgui.ListItem(title, iconImage = FANART)
      item.setInfo('video', infoLabels)
      item.setProperty('IsPlayable', 'true')
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?vaata=%s' %  s.group(1), item))
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)     
    #<a href="arhiiv.php?id=136729"><b>Terevisioon</b> (11.03.2013 06:55)</a>
    
  def getMediaLocation(self,key):
    url = "http://etv.err.ee/arhiiv.php?id=%s" % key
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if html:
      #loadFlow('flow_player', 'rtmp://media.err.ee/etvsaated','mp4:2013-002695-0010_Kahekone(SUB).mp4',null,0,true);
      key = re.search('loadFlow.*\'rtmp([^\']+).*mp4:([^\']+)', html, re.DOTALL)
      if key:
	return 'rtmp' + key.group(1) + '/' + key.group(2)
    else:
      raise EtvException(ADDON.getLocalizedString(202))
    
  def playStream(self,vaata):
    saade = EtvAddon.getMediaLocation(vaata)
    buggalo.addExtraData('saade', saade)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    item = xbmcgui.ListItem(saade, iconImage = ICON, path = saade)
    playlist.add(saade,item)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)

  def displayError(self, message = 'n/a'):
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
  FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
  
  CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
  if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)
    

  buggalo.SUBMIT_URL = 'http://loru.mine.nu/exception/submit.php'
  
  EtvAddon = Etv()
  try:
    if PARAMS.has_key('channel') and PARAMS.has_key('date'):
      EtvAddon.listSchedule(PARAMS['channel'][0], PARAMS['date'][0])
    elif PARAMS.has_key('channel'):
      EtvAddon.listDates(PARAMS['channel'][0])
    elif PARAMS.has_key('vaata'):
      EtvAddon.playStream(PARAMS['vaata'][0])
    else:
      EtvAddon.listChannels()
  except EtvException, ex:
    EtvAddon.displayError(str(ex))
  except Exception:
    buggalo.onExceptionRaised()
