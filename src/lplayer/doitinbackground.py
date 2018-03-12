#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of slimbooktouchpad
#
# Copyright (C) 2016-2018 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
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
    exit(-1)
from gi.repository import GObject
from gi.repository import GLib
from threading import Thread
import time


class IdleObject(GObject.GObject):
    """
    Override GObject.GObject to always emit signals in the main thread
    by emmitting on an idle handler
    """
    def __init__(self):
        GObject.GObject.__init__(self)

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)


class DoItInBackground(IdleObject, Thread):
    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int, )),
        'ended': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'done_one': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                     (str,)),
        'started_one': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                        (str,))
    }

    def __init__(self, callback, args):
        IdleObject.__init__(self)
        Thread.__init__(self)
        self.daemon = True
        self.stopit = False
        self.ok = True
        self.callback = callback
        self.args = args

    def stop(self, *args):
        self.stopit = True

    def run(self):
        self.emit('started', len(self.args))
        for index, arg in enumerate(self.args):
            if self.stopit is True:
                break
            self.emit('started_one', arg)
            self.callback(arg)
            self.emit('done_one', arg)
        self.emit('ended', self.ok)


if __name__ == '__main__':
    from progressdialog import ProgressDialog

    def test(arg):
        def feed(self, astring):
            print(arg)

    commands = ['ls', 'ls -la', 'ls']
    diib = DoItInBackground(test, commands)
    progreso = ProgressDialog('Adding new ppa', None)
    progreso.set_number_of_elements(len(commands))
    diib.connect('started_one', progreso.set_element)
    # diib.connect('done_one', progreso.increase)
    diib.connect('ended', progreso.close)
    progreso.connect('i-want-stop', diib.stop)
    diib.start()
    progreso.run()
    time.sleep(10)
