#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# donwloader.py
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
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import GLib
from gi.repository import GObject
import threading
import requests
import os
import shlex
import subprocess
from . import comun


def convert2ogg(filein, fileout):
    rutine = 'ffmpeg -i "%s" -vn -acodec libvorbis -y "%s"' % (
        filein, fileout)
    args = shlex.split(rutine)
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    out, err = process.communicate()
    if err is None:
        return True
    return False


class Downloader(threading.Thread, GObject.GObject):
    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'ended': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'failed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, row):
        threading.Thread.__init__(self)
        GObject.GObject.__init__(self)
        self.row = row
        self.daemon = True

    def get_row(self):
        return self.row

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def run(self):
        try:
            self.emit('started')
            extension = self.row.audio['ext']
            audio_id = self.row.audio['display_id']
            url = self.row.audio['download_url']
            filein = os.path.join(
                comun.AUDIO_DIR,
                '{0}.{1}'.format(audio_id, extension))
            fileout = os.path.join(
                comun.AUDIO_DIR,
                '{0}.{1}'.format(audio_id, 'ogg'))
            r = requests.get(url, stream=True)
            if os.path.exists(fileout):
                self.emit('ended')
            else:
                if not os.path.exists(filein):
                    with open(filein, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            print(chunk)
                            if chunk:
                                f.write(chunk)
                is_converted = convert2ogg(filein, fileout)
                if not is_converted:
                    if os.path.exists(fileout):
                        os.remove(fileout)
                if os.path.exists(filein):
                    os.remove(filein)
                if is_converted is True:
                    self.emit('ended')
                else:
                    self.emit('failed')
        except Exception as e:
            print(e)
            self.emit('failed')
