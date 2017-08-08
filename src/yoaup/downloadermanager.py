#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# downloadermanager.py
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


import gi
try:
    gi.require_version('GObject', '2.0')
    gi.require_version('GLib', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import GObject
from gi.repository import GLib
from .downloader import Downloader

MAX_DOWNLOADERS = 4


class DownloaderManager(GObject.GObject):
    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'ended': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
        'failed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object,)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.downloaders = []
        self.queue = []
        self.tries = 0

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def on_downloader_ended(self, widget, downloader):
        self.emit('ended', downloader.get_row())
        self.downloaders.remove(downloader)
        if len(self.queue) > 0:
            new_row = self.queue.pop()
            self.download(new_row)

    def on_downloader_failed(self, widget, downloader):
        self.emit('failed', downloader.get_row())
        if self.tries < 3:
            self.downloaders.remove(downloader)
            self.queue.insert(0, downloader.get_row())
        else:
            self.tries = 0
        if len(self.queue) > 0:
            new_row = self.queue.pop()
            if new_row == downloader.get_row():
                self.tries += 1
            self.download(new_row)

    def add(self, row):
        print('add')
        if len(self.downloaders) < MAX_DOWNLOADERS:
            self.download(row)
        else:
            self.queue.insert(0, row)

    def download(self, row):
        downloader = Downloader(row)
        downloader.connect('ended', self.on_downloader_ended, downloader)
        downloader.connect('failed', self.on_downloader_failed, downloader)
        downloader.start()
        self.downloaders.append(downloader)
        self.emit('started', row)
