#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# youtube_utils.py
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


import sys

try:
    import youtube_dl
except Exception as e:
    sys.path.insert(1, '/usr/lib/python2.7/dist-packages/')
    import youtube_dl
from .audio import Audio


def resolve_youtube_url(url):
    audio = None
    if url is not None and (url.startswith('http://') or
                            url.startswith('https://')):
        try:
            ydl_opts = {
                'outtmpl': '%(id)s%(ext)s',
            }
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            ydl.add_default_info_extractors()
            info = ydl.extract_info(url, download=False)
            audio = Audio(url,
                          display_id=info['display_id'],
                          description=info['description'],
                          duration=info['duration'],
                          creator=info['creator'],
                          thumbnail=info['thumbnail'],
                          title=info['title'],
                          upload_date=info['upload_date'])
            min_size = -1
            for aformat in info['formats']:
                if aformat['format'].find('audio only') > -1:
                    print('=!!=', aformat['filesize'])
                    if aformat['filesize'] is not None and (
                            min_size == -1 or
                            min_size > int(aformat['filesize'])):
                        min_size = aformat['filesize']
                        selected_format = aformat
            audio['ext'] = selected_format['ext']
            audio['filesize'] = selected_format['filesize']
            audio['download_url'] = selected_format['url']
        except Exception as e:
            print('******', str(e), '*********')
            audio = None
    return audio


if __name__ == '__main__':
    print(1)
    url = 'https://www.youtube.com/watch?v=bHZ8KUrbbcc'
    print(resolve_youtube_url(url))
