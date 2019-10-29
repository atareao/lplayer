#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of lplayer
#
# Copyright (c) 2017-2019 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import locale
import gettext

__author__ = 'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'
__copyright__ = 'Copyright (c) 2017 Lorenzo Carbonell'
__license__ = 'GPLV3'
__url__ = 'http://www.atareao.es'
USRDIR = '/usr'


def is_package():
    return (__file__.startswith(USRDIR) or os.getcwd().startswith(USRDIR))


PARAMS = {'first-time': True,
          'version': None,
          'speed': 1.0,
          'remove_silence': False,
          'equalizer': {'band0': 0, 'band1': 0, 'band2': 0, 'band3': 0,
                        'band4': 0, 'band5': 0, 'band6': 0, 'band7': 0,
                        'band8': 0, 'band9': 0, 'band10': 0, 'band11': 0,
                        'band12': 0, 'band13': 0, 'band14': 0, 'band15': 0,
                        'band16': 0, 'band17': 0},
          'play_continuously': False,
          'download_on_added': False,
          'remove_on_listened': False,
          'row': 0,
          'audios': [],
          'preset': 'none'
          }


APP = 'lplayer'
APPCONF = APP + '.conf'
APPDATA = APP + '.data'
APPNAME = 'lplayer'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
AUDIO_DIR = os.path.join(CONFIG_APP_DIR, 'audio')
THUMBNAILS_DIR = os.path.join(CONFIG_APP_DIR, 'thumbnails')
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APPCONF)
AUTOSTART_DIR = os.path.join(CONFIG_DIR, 'autostart')
FILE_AUTO_START = os.path.join(AUTOSTART_DIR,
                               'lplayer-autostart.desktop')
if not os.path.exists(CONFIG_APP_DIR):
    os.makedirs(CONFIG_APP_DIR)
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

if is_package():
    ROOTDIR = '/usr/share/'
    if 'SNAP' in os.environ:
        ROOTDIR = os.environ["SNAP"] + ROOTDIR
    LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
    APPDIR = os.path.join(ROOTDIR, APP)
    ICONDIR = os.path.join(APPDIR, 'icons')
    CHANGELOG = os.path.join(APPDIR, 'changelog')
    FILE_AUTO_START_ORIG = os.path.join(APPDIR,
                                        'lplayer-autostart.desktop')
else:
    ROOTDIR = os.path.dirname(__file__)
    LANGDIR = os.path.join(ROOTDIR, 'template1')
    APPDIR = os.path.join(ROOTDIR, APP)

    ICONDIR = os.path.normpath(os.path.join(ROOTDIR, '../../data/icons'))
    DEBIANDIR = os.path.normpath(os.path.join(ROOTDIR, '../../debian'))
    CHANGELOG = os.path.join(DEBIANDIR, 'changelog')
    FILE_AUTO_START_ORIG = os.path.join(os.path.normpath(os.path.join(
        ROOTDIR, '../data')), 'lplayer-autostart.desktop')
PLAY_ICON = os.path.join(ICONDIR, 'play.svg')
PAUSE_ICON = os.path.join(ICONDIR, 'pause.svg')
WAIT_ICON = os.path.join(ICONDIR, 'wait.svg')
DOWNLOAD_ICON = os.path.join(ICONDIR, 'download.svg')
DELETE_ICON = os.path.join(ICONDIR, 'delete.svg')
INFO_ICON = os.path.join(ICONDIR, 'info.svg')
NOIMAGE_ICON = os.path.join(ICONDIR, 'podcastnoimage.svg')
LISTENED_ICON = os.path.join(ICONDIR, 'listened.svg')
NOLISTENED_ICON = os.path.join(ICONDIR, 'nolistened.svg')
DOWNLOAD_ANIM = os.path.join(ICONDIR, 'loading.gif')
ICON = os.path.join(ICONDIR, 'lplayer.svg')


f = open(CHANGELOG, 'r')
line = f.readline()
f.close()
pos = line.find('(')
posf = line.find(')', pos)
VERSION = line[pos + 1:posf].strip()
if not is_package():
    VERSION = VERSION + '-src'

try:
    current_locale, encoding = locale.getdefaultlocale()
    language = gettext.translation(APP, LANGDIR, [current_locale])
    language.install()
    _ = language.gettext
except Exception as e:
    _ = str
