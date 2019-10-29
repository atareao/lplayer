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
    gi.require_version('GdkPixbuf', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import GdkPixbuf
import base64
import os
import re
import subprocess
import io
from PIL import Image
try:
    from . import comun
except Exception as e:
    import sys
    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                 os.path.expanduser(__file__))))
    sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
    import comun


NOIMAGE = GdkPixbuf.Pixbuf.new_from_file_at_size(comun.NOIMAGE_ICON, 256, 256)


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[0]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_selected_value_in_combo(combo):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 0)


def get_pixbuf_from_base64string(base64string):
    if base64string is None:
        return NOIMAGE
    raw_data = base64.b64decode(base64string.encode())
    try:
        pixbuf_loader = GdkPixbuf.PixbufLoader.new_with_mime_type("image/jpeg")
        pixbuf_loader.write(raw_data)
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        return pixbuf
    except Exception as e:
        print(e)
    try:
        pixbuf_loader = GdkPixbuf.PixbufLoader.new_with_mime_type("image/png")
        pixbuf_loader.write(raw_data)
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        return pixbuf
    except Exception as e:
        print(e)
    return NOIMAGE

def get_thumbnail_filename_for_audio(audio):
    thumbnail_filename = os.path.join(comun.THUMBNAILS_DIR,
                                      '{0}.png'.format(audio['hash']))
    if not os.path.exists(thumbnail_filename):
        pixbuf = get_pixbuf_from_base64string(audio['thumbnail_base64'])
        pixbuf.savev(thumbnail_filename, 'png', [], [])
    return thumbnail_filename


def create_thumbnail_for_audio(hash, thumbnail_base64):
    thumbnail_filename = os.path.join(comun.THUMBNAILS_DIR,
                                      '{0}.png'.format(hash))
    if not os.path.exists(thumbnail_filename):
        if thumbnail_base64 is not None:
            pixbuf = get_pixbuf_from_base64string(thumbnail_base64)
        else:
            pixbuf = NOIMAGE
        pixbuf = pixbuf.scale_simple(256, 256, GdkPixbuf.InterpType.BILINEAR)
        pixbuf.savev(thumbnail_filename, 'png', [], [])


def is_running(process):
    # From http://www.bloggerpolis.com/2011/05/\
    # how-to-check-if-a-process-is-running-using-python/
    # and http://richarddingwall.name/2009/06/18/\
    # windows-equivalents-of-ps-and-kill-commands/
    try:  # Linux/Unix
        s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    except Exception as e:  # Windows
        print(e)
        s = subprocess.Popen(["tasklist", "/v"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x.decode()):
            return True
    return False


def get_desktop_environment():
    desktop_session = os.environ.get("DESKTOP_SESSION")
    # easier to match if we doesn't have  to deal with caracter cases
    if desktop_session is not None:
        desktop_session = desktop_session.lower()
        if desktop_session in ["gnome", "unity", "cinnamon", "mate",
                               "budgie-desktop", "xfce4", "lxde", "fluxbox",
                               "blackbox", "openbox", "icewm", "jwm",
                               "afterstep", "trinity", "kde"]:
            return desktop_session
        # ## Special cases ##
        # Canonical sets $DESKTOP_SESSION to Lubuntu rather than
        # LXDE if using LXDE.
        # There is no guarantee that they will not do the same with
        # the other desktop environments.
        elif "xfce" in desktop_session or\
                desktop_session.startswith("xubuntu"):
            return "xfce4"
        elif desktop_session.startswith("ubuntu"):
            return "unity"
        elif desktop_session.startswith("lubuntu"):
            return "lxde"
        elif desktop_session.startswith("kubuntu"):
            return "kde"
        elif desktop_session.startswith("razor"):  # e.g. razorkwin
            return "razor-qt"
        elif desktop_session.startswith("wmaker"):  # eg. wmaker-common
            return "windowmaker"
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        return "kde"
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        if "deprecated" not in os.environ.get(
                'GNOME_DESKTOP_SESSION_ID'):
            return "gnome2"
    # From http://ubuntuforums.org/showthread.php?t=652320
    elif is_running("xfce-mcs-manage"):
        return "xfce4"
    elif is_running("ksmserver"):
        return "kde"
    return "unknown"


if __name__ == '__main__':
    print(get_desktop_environment())
