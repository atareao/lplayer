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


import codecs
import os
import json

from . import comun


class Configuration(object):
    def __init__(self):
        self.params = comun.PARAMS
        self.check()
        self.read()

    def check(self):
        if not os.path.exists(comun.CONFIG_APP_DIR):
            os.makedirs(comun.CONFIG_APP_DIR)

    def get(self, key):
        try:
            return self.params[key]
        except KeyError as e:
            print(e)
            self.params[key] = comun.PARAMS[key]
            return self.params[key]

    def set(self, key, value):
        self.params[key] = value

    def reset(self):
        if os.path.exists(comun.CONFIG_FILE):
            os.remove(comun.CONFIG_FILE)
        self.params = comun.PARAMS
        self.save()

    def set_defaults(self):
        self.params = comun.PARAMS
        self.save()

    def read(self):
        self.check()
        try:
            f = codecs.open(comun.CONFIG_FILE, 'r', 'utf-8')
        except IOError as e:
            print(e)
            self.save()
            f = codecs.open(comun.CONFIG_FILE, 'r', 'utf-8')
        try:
            self.params = json.loads(f.read())
        except ValueError as e:
            print(e)
            self.save()
        f.close()

    def save(self):
        self.check()
        f = codecs.open(comun.CONFIG_FILE, 'w', 'utf-8')
        f.write(json.dumps(self.params, indent=4, sort_keys=True))
        f.close()

    def __str__(self):
        ans = ''
        for key in sorted(self.params.keys()):
            ans += '{0}: {1}\n'.format(key, self.params[key])
        return ans

