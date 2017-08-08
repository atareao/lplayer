#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# youttubegetter.py
#
# This file is part of yoaup (YouTube Audio Player)
#
# Copyright (C) 2017
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import urllib.request
import pprint
import requests
import sys
from urllib.parse import unquote_plus
try:
    import youtube_dl
except:
    sys.path.insert(1, '/usr/lib/python2.7/dist-packages/')
    import youtube_dl


url = 'https://www.youtube.com/watch?v=MkZ1OeSR2Uo'
ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})
ydl.add_default_info_extractors()
result = ydl.extract_info(url, download=False)
print('***********************+')
pprint.pprint(result)
print('***********************+')
pprint.pprint(result['formats'])


print('----', url, '----')




class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13)\
 Gecko/20101230 Mandriva Linux/1.9.2.13-0.2mdv2010.2 (2010.2) Firefox/3.6.13"


if len(sys.argv) < 2:
    print('Usage: {prog} URL'.format(prog=sys.argv[0]))
    #sys.exit(1)
    video_id = 'MkZ1OeSR2Uo'
else:
    video_id = sys.argv[1]

opener = AppURLopener()
fp = opener.open('http://www.youtube.com/get_video_info?video_id={vid}'.format(
    vid=video_id))
data = fp.read()
fp.close()

response = requests.get('http://www.youtube.com/get_video_info?video_id={vid}'.format(
    vid=video_id))
print(response.text.startswith('status=fail'))
if response.status_code == 200 and not response.text.startswith('status=fail'):
    vid_list = []
    for fmt_chk in unquote_plus(unquote_plus(response.text)).split('|'):
        print(fmt_chk)
        if len(fmt_chk) == 0:
            continue
        if not fmt_chk.startswith('http://') or not fmt_chk.startswith('https://'):
            continue
        vid_list.append(fmt_chk)
    print(vid_list)


if data.startswith('status=fail'):
    print('Error: Video not found!')
    sys.exit(2)

vid_list = []
tmp_list = urllib.unquote(urllib.unquote(data)).split('|')
for fmt_chk in tmp_list:
    if len(fmt_chk) == 0:
        continue
    if not fmt_chk.startswith('http://'):
        continue
    vid_list.append(fmt_chk)

# FIXME: Format choice
link = vid_list[0]

fp = opener.open(link)
data = fp.read(1024)
while data:
    sys.stdout.write(data)
    data = fp.read(1024)
fp.close()
