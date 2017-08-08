#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# listboxrowwithdata.py
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
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('Gio', '2.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
    gi.require_version('GdkPixbuf', '2.0')
    gi.require_version('Notify', '0.7')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf
import time
import os
from .utils import get_pixbuf_from_base64string
from . import comun

PLAY = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.PLAY_ICON, 32, 32)
INFO = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.INFO_ICON, 16, 16)
PAUSE = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.PAUSE_ICON, 32, 32)
DOWNLOAD = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.DOWNLOAD_ICON, 32, 32)
DOWNLOAD_ANIM = GdkPixbuf.PixbufAnimation.new_from_file(comun.DOWNLOAD_ANIM)
LDOWNLOAD = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.DOWNLOAD_ICON, 16, 16)
LDELETE = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.DELETE_ICON, 16, 16)
LWAIT = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.WAIT_ICON, 16, 16)
LISTENED = GdkPixbuf.Pixbuf.new_from_file_at_size(
    comun.LISTENED_ICON, 16, 16)
NOLISTENED = GdkPixbuf.Pixbuf.new_from_file_at_size(
    comun.NOLISTENED_ICON, 16, 16)


class ListBoxRowWithData(Gtk.ListBoxRow):
    __gsignals__ = {
        'button_play_pause_clicked': (GObject.SIGNAL_RUN_FIRST,
                                      GObject.TYPE_NONE, ()),
        'button_info_clicked': (GObject.SIGNAL_RUN_FIRST,
                                GObject.TYPE_NONE, ()),
        'button_download_clicked': (GObject.SIGNAL_RUN_FIRST,
                                    GObject.TYPE_NONE, ()),
        'button_listened_clicked': (GObject.SIGNAL_RUN_FIRST,
                                    GObject.TYPE_NONE, ()),
        'end': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, audio, index):
        super(Gtk.ListBoxRow, self).__init__()
        self.set_name('listboxrowwithdata')
        grid = Gtk.Grid()
        self.add(grid)

        self.image = Gtk.Image()
        self.image.set_margin_top(5)
        self.image.set_margin_bottom(5)
        self.image.set_margin_left(5)
        self.image.set_margin_right(5)
        grid.attach(self.image, 0, 0, 4, 4)

        self.label1 = Gtk.Label()
        self.label1.set_name('label')
        self.label1.set_margin_top(5)
        self.label1.set_alignment(0, 0.5)
        grid.attach(self.label1, 4, 0, 1, 1)

        self.label2 = Gtk.Label()
        self.label2.set_valign(Gtk.Align.FILL)
        self.label2.set_line_wrap(True)
        self.label2.set_alignment(0, 0.5)
        grid.attach(self.label2, 4, 1, 1, 1)

        self.label3 = Gtk.Label()
        self.label3.set_alignment(0, 0.5)
        grid.attach(self.label3, 4, 2, 1, 1)

        self.label4 = Gtk.Label()
        self.label4.set_alignment(0, 0.5)
        self.label4.set_margin_right(5)
        self.label4.set_halign(Gtk.Align.END)
        grid.attach(self.label4, 5, 2, 1, 1)

        self.button_listened = Gtk.Button()
        self.button_listened.set_name('button')
        self.button_listened.connect('clicked',
                                     self.on_button_clicked,
                                     'listened')

        self.listened = Gtk.Image()
        self.listened.set_from_pixbuf(NOLISTENED)
        self.listened.set_margin_left(5)
        self.button_listened.add(self.listened)
        grid.attach(self.button_listened, 6, 0, 1, 1)

        self.button_download = Gtk.Button()
        self.button_download.set_name('button')
        self.button_download.connect('clicked',
                                     self.on_button_clicked,
                                     'download')

        self.download = Gtk.Image()
        self.download.set_from_pixbuf(LDOWNLOAD)
        self.download.set_margin_left(5)
        self.button_download.add(self.download)
        grid.attach(self.button_download, 6, 1, 1, 1)

        self.button_info = Gtk.Button()
        self.button_info.set_name('button')
        self.button_info.connect('clicked',
                                 self.on_button_clicked,
                                 'info')

        info = Gtk.Image()
        info.set_from_pixbuf(INFO)
        info.set_margin_left(5)
        self.button_info.add(info)
        grid.attach(self.button_info, 6, 2, 1, 1)

        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_margin_bottom(5)
        self.progressbar.set_valign(Gtk.Align.CENTER)
        self.progressbar.set_hexpand(True)
        self.progressbar.set_margin_right(5)
        grid.attach(self.progressbar, 4, 3, 2, 1)

        self.button_play_pause = Gtk.Button()
        self.button_play_pause.set_name('button')
        self.button_play_pause.connect('clicked',
                                       self.on_button_clicked,
                                       'play_pause')
        self.button_play_pause.set_margin_top(5)
        self.button_play_pause.set_margin_bottom(5)
        self.button_play_pause.set_margin_left(5)
        self.button_play_pause.set_margin_right(5)
        self.play_pause = Gtk.Image()
        self.play_pause.set_margin_left(5)
        self.button_play_pause.add(self.play_pause)
        grid.attach(self.button_play_pause, 7, 0, 4, 4)

        self.is_playing = False
        self.is_downloading = False
        self.index = index
        self.set_audio(audio)

    def can_play(self):
        return (self.is_downloading is False and
                self.audio['downloaded'] is True)

    def click_button_play(self):
        if self.audio['downloaded'] is True:
            self.emit('button_play_pause_clicked')

    def on_button_clicked(self, widget, button_name):
        if button_name == 'info':
            self.emit('button_info_clicked')
        elif button_name == 'play_pause':
            self.emit('button_play_pause_clicked')
        elif button_name == 'download':
            self.emit('button_download_clicked')
            self.download.set_from_pixbuf(LWAIT)
        elif button_name == 'listened':
            self.emit('button_listened_clicked')

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def set_downloading(self, downloading):
        self.is_downloading = downloading
        if downloading is True:
            self.play_pause.set_from_animation(DOWNLOAD_ANIM)
        else:
            if self.audio['downloaded'] is True:
                if self.is_playing is True:
                    self.play_pause.set_from_pixbuf(PAUSE)
                else:
                    self.play_pause.set_from_pixbuf(PLAY)
            else:
                self.play_pause.set_from_pixbuf(PLAY)

    def set_downloaded(self, downloaded):
        '''
        if downloaded is False:
            extension = self.audio['ext']
            audio_id = self.audio['display_id']
            filein = os.path.join(
                comun.AUDIO_DIR,
                '{0}.{1}'.format(audio_id, extension))
            fileout = os.path.join(
                comun.AUDIO_DIR,
                '{0}.{1}'.format(audio_id, 'ogg'))
            if os.path.exists(filein):
                os.remove(filein)
            if os.path.exists(fileout):
                os.remove(fileout)
        '''
        self.audio['downloaded'] = downloaded
        self.button_play_pause.set_sensitive(downloaded)
        if downloaded is True:
            self.download.set_from_pixbuf(LDELETE)
        else:
            self.download.set_from_pixbuf(LDOWNLOAD)

    def set_playing(self, playing):
        print('id', self.index, 'is_playing', playing)
        self.is_playing = playing
        if self.is_playing is True:
            self.play_pause.set_from_pixbuf(PAUSE)
        else:
            self.play_pause.set_from_pixbuf(PLAY)

    def __eq__(self, other):
        return self.audio['display_id'] == other.audio['display_id']

    def set_duration(self, duration):
        self.audio['duration'] = duration
        self.label4.set_text(time.strftime('%H:%M:%S', time.gmtime(duration)))

    def get_duration(self):
        return self.audio['duration']

    def get_position(self):
        return self.audio['position']

    def set_listened(self, listened):
        self.audio['listened'] = listened
        if listened is True:
            self.listened.set_from_pixbuf(LISTENED)
        else:
            self.listened.set_from_pixbuf(NOLISTENED)

    def set_position(self, position):
        self.audio['position'] = position
        self.label3.set_text(time.strftime('%H:%M:%S', time.gmtime(
            self.audio['duration'] * position)))
        self.progressbar.set_fraction(position)

    def set_audio(self, audio):
        self.audio = audio
        pixbuf = get_pixbuf_from_base64string(
            audio['thumbnail_base64']).scale_simple(
            64, 64, GdkPixbuf.InterpType.BILINEAR)
        self.image.set_from_pixbuf(pixbuf)
        if len(audio['title']) > 35:
            feed_name = audio['title'][:32] + '...'
        else:
            feed_name = audio['title']
        self.label1.set_markup(
            '<big><b>{0}</b></big>'.format(feed_name))
        self.label2.set_text(audio['title'])
        if audio['listened'] is True:
            self.listened.set_from_pixbuf(LISTENED)
        else:
            self.listened.set_from_pixbuf(NOLISTENED)
        self.set_downloaded(audio['downloaded'])
        self.set_duration(audio['duration'])
        self.set_position(audio['position'])
        self.play_pause.set_from_pixbuf(PLAY)
        self.is_playing = False
        self.is_downloading = False
