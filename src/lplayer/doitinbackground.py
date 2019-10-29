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
