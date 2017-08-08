#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# audio.py
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


class Audio(dict):
    def __init__(self, url, download_url=None, display_id=None,
                 description=None, duration=-1, ext=None, filesize=-1,
                 creator=None, thumbnail=None, title=None, upload_date=None):
        self['url'] = url
        self['download_url'] = download_url
        self['display_id'] = display_id
        self['description'] = description
        self['duration'] = duration
        self['ext'] = ext
        self['filesize'] = filesize
        self['creator'] = creator
        self['thumbnail'] = thumbnail
        self['thumbnail_base64'] = None
        self['title'] = title
        self['upload_date'] = upload_date
        self['downloaded'] = False
        self['listened'] = False
        self['position'] = 0
        self['norder'] = -1
    '''
    def __str__(self):
        astr = 'url: {0}\ndownload_url: {1}\ndisplay_id: {2}\n\
description: {3}\nduration: {4}\next: {5}\nfilesize: {6}\ncreator: {7}\n\
thumbnail: {8}\nthumbnail_base64: {9}\ntitle: {10}\nupload_date: {11}\n\
downloaded: {12}\nlistened: {13}\nposition: {14}\nnorder: {15}\n'
        return astr.format(self.url, self.download_url, self.display_id,
                           self.description, self.duration, self.ext,
                           self.filesize, self.creator, self.thumbnail,
                           self.thumbnail_base64, self.title, self.upload_date,
                           self.is_downloaded, self.is_listened,
                           self.position, self.norder)
    '''

    def __eq__(self, other):
        return self['display_id'] == other['display_id']

    def get_dict(self):
        ans = {}
        ans['url'] = self.url
        ans['download_url'] = self.download_url
        ans['display_id'] = self.display_id
        ans['description'] = self.description
        ans['duration'] = self.duration
        ans['ext'] = self.ext
        ans['filesize'] = self.filesize
        ans['creator'] = self.creator
        ans['thumbnail'] = self.thumbnail
        ans['thumbnail_base64'] = self.thumbnail_base64
        ans['title'] = self.title
        ans['upload_date'] = self.upload_date
        ans['downloaded'] = self.is_downloaded
        ans['listened'] = self.is_listened
        ans['position'] = self.position
        ans['norder'] = self.norder
        return ans

    def set_dict(self, ans):
        self.url = ans['url']
        self.download_url = ans['download_url']
        self.display_id = ans['display_id']
        self.description = ans['description']
        self.duration = ans['duration']
        self.ext = ans['ext']
        self.filesize = ans['filesize']
        self.creator = ans['creator']
        self.thumbnail = ans['thumbnail']
        self.thumbnail_base64 = ans['thumbnail_base64']
        self.title = ans['title']
        self.upload_date = ans['upload_date']
        self.is_downloaded = ans['downloaded']
        self.is_listened = ans['listened']
        self.position = ans['position']
        self.norder = ans['norder']
