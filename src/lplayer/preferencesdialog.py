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
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from .configurator import Configuration
from . import comun
from .comun import _


class PreferencesDialog(Gtk.Dialog):
    """docstring for PreferencesDialog"""
    def __init__(self, window):
        #
        Gtk.Dialog.__init__(self, '{0} | {1}'.format(
            comun.APPNAME, _('Preferences')),
            window,
            Gtk.DialogFlags.MODAL |
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)

        frame = Gtk.Frame.new('Track options')
        frame.set_margin_top(5)
        frame.set_margin_bottom(5)
        frame.set_margin_left(5)
        frame.set_margin_right(5)
        self.get_content_area().add(frame)

        grid = Gtk.Grid()
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        frame.add(grid)

        label = Gtk.Label('Must I download audio when it just added?')
        label.set_alignment(0, 0.5)
        grid.attach(label, 0, 0, 1, 1)

        self.download_on_added = Gtk.Switch()
        grid.attach(self.download_on_added, 1, 0, 1, 1)

        label = Gtk.Label('Must I remove audio when you listened it?')
        label.set_alignment(0, 0.5)
        grid.attach(label, 0, 1, 1, 1)

        self.remove_on_listened = Gtk.Switch()
        grid.attach(self.remove_on_listened, 1, 1, 1, 1)

        self.load_preferences()

        self.show_all()

    def load_preferences(self):
        configuration = Configuration()
        self.download_on_added.set_active(
            configuration.get('download_on_added'))
        self.remove_on_listened.set_active(
            configuration.get('remove_on_listened'))

    def save_preferences(self):
        print(1)
        configuration = Configuration()
        print(2)
        configuration.set('download_on_added',
                          self.download_on_added.get_active())
        print(3)
        configuration.set('remove_on_listened',
                          self.remove_on_listened.get_active())
        print(4)
        configuration.save()
        print(configuration)
        print(5)


if __name__ == '__main__':
    sid = PreferencesDialog(None)
    if sid.run() == Gtk.ResponseType.ACCEPT:
        sid.hide()
        sid.save_preferences()
    sid.destroy()
