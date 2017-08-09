#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preferencesdialog.py
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
