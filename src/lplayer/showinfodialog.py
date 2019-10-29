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

import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import GdkPixbuf
import os
try:
    from . import comun
    from .comun import _
except Exception as e:
    import sys
    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                 os.path.expanduser(__file__))))
    sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
    import comun
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

        filename = os.path.join(
            comun.THUMBNAILS_DIR, '{0}.png'.format(audio['hash']))
        if os.path.exists(filename):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                filename, 256, 256)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                comun.NOIMAGE_ICON, 256, 256)
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
