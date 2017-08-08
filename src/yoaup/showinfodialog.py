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
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk

'''
import os
import sys
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                             os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
import comun
from comun import _
'''
from . import comun
from .comun import _


class ShowInfoDialog(Gtk.Dialog):
    """docstring for AddFeedDialog"""
    def __init__(self, window, podcast_text, title_text, link_text, text):
        #
        Gtk.Dialog.__init__(self, '{0} | {1}'.format(
            comun.APPNAME, _('Show info about podcast')),
            window,
            Gtk.DialogFlags.MODAL |
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)

        frame = Gtk.Frame.new(podcast_text)
        frame.set_margin_top(10)
        frame.set_margin_bottom(10)
        frame.set_margin_left(10)
        frame.set_margin_right(10)
        self.get_content_area().add(frame)

        grid = Gtk.Grid()
        frame.add(grid)

        title = Gtk.Entry()
        title.set_text(title_text)
        title.set_editable(False)
        title.set_margin_top(10)
        title.set_margin_bottom(5)
        title.set_margin_left(10)
        title.set_margin_right(10)
        grid.attach(title, 0, 0, 1, 1)

        framesw = Gtk.Frame()
        framesw.set_margin_top(5)
        framesw.set_margin_bottom(10)
        framesw.set_margin_left(10)
        framesw.set_margin_right(10)
        grid.attach(framesw, 0, 1, 1, 1)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_visible(True)
        scrolledwindow.set_size_request(500, 500)
        scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.AUTOMATIC)
        framesw.add(scrolledwindow)

        textView = Gtk.TextView()
        textView.set_wrap_mode(Gtk.WrapMode.WORD)
        textView.set_editable(False)
        scrolledwindow.add(textView)
        textView.get_buffer().set_text(text)

        link = Gtk.LinkButton.new(link_text)
        link.set_margin_top(5)
        link.set_margin_bottom(5)
        link.set_margin_left(10)
        link.set_margin_right(10)
        grid.attach(link, 0, 2, 1, 1)

        self.show_all()


if __name__ == '__main__':
    sid = ShowInfoDialog(None, 'uGeek', 'El título', 'https://www.atareao.es',
                         'Esto es una prueba')
    sid.run()
