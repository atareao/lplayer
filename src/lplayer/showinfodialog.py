#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# showinfodialog.py
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
    gi.require_version('GdkPixbuf', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import GdkPixbuf

try:
    from . import comun
    from .comun import _
    from .utils import get_pixbuf_from_base64string
except Exception as e:
    import os
    import sys
    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                 os.path.expanduser(__file__))))
    sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
    import comun
    from utils import get_pixbuf_from_base64string
    from audio import Audio
    from comun import _


class ShowInfoDialog(Gtk.Dialog):
    """docstring for AddFeedDialog"""
    def __init__(self, window, audio):
        #
        Gtk.Dialog.__init__(self, '{0} | {1}'.format(
            comun.APPNAME, _('Show info about audio')),
            window,
            Gtk.DialogFlags.MODAL |
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)

        frame = Gtk.Frame.new('')
        frame.set_margin_top(10)
        frame.set_margin_bottom(10)
        frame.set_margin_left(10)
        frame.set_margin_right(10)
        self.get_content_area().add(frame)

        grid = Gtk.Grid()
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        frame.add(grid)

        image = Gtk.Image()
        grid.attach(image, 0, 0, 4, 4)
        pixbuf = get_pixbuf_from_base64string(
            audio['thumbnail_base64']).scale_simple(
            256, 256, GdkPixbuf.InterpType.BILINEAR)
        image.set_from_pixbuf(pixbuf)

        label = Gtk.Label(_('Artist') + ': ')
        label.set_alignment(0, 0.5)
        grid.attach(label, 5, 0, 1, 1)
        title = Gtk.Entry()
        title.set_text(audio['artist'])
        title.set_editable(False)
        grid.attach(title, 6, 0, 1, 1)

        label = Gtk.Label(_('Album') + ': ')
        label.set_alignment(0, 0.5)
        grid.attach(label, 5, 1, 1, 1)
        album = Gtk.Entry()
        album.set_text(audio['album'])
        album.set_editable(False)
        grid.attach(album, 6, 1, 1, 1)

        label = Gtk.Label(_('Title') + ': ')
        label.set_alignment(0, 0.5)
        grid.attach(label, 5, 2, 1, 1)
        title = Gtk.Entry()
        title.set_text(audio['title'])
        title.set_editable(False)
        grid.attach(title, 6, 2, 1, 1)

        label = Gtk.Label(_('Year') + ': ')
        label.set_alignment(0, 0.5)
        grid.attach(label, 5, 3, 1, 1)
        year = Gtk.Entry()
        year.set_text(audio['year'])
        year.set_editable(False)
        grid.attach(year, 6, 3, 1, 1)

        self.show_all()


if __name__ == '__main__':
    audio = Audio(
        '/home/lorenzo/Descargas/Telegram Desktop/02. Jenifer - Sur Le Fil.mp3')
    sid = ShowInfoDialog(None, audio)
    sid.run()
