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
    gi.require_version('AppIndicator3', '0.1')
    gi.require_version('Gtk', '3.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('GdkPixbuf', '2.0')
except Exception as e:
    print(e)
    print('Repository version required not present')
    exit(1)
from gi.repository import AppIndicator3
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import GdkPixbuf
import os
import webbrowser
from .comun import _
from . import comun
PLAY = 'media-playback-start-symbolic'
PAUSE = 'media-playback-pause-symbolic'


class Indicator(GObject.Object):
    __gsignals__ = {
        'play': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'pause': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'previous': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
        'next': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, main_window):
        GObject.GObject.__init__(self)
        self.main_window = main_window
        self.indicator = AppIndicator3.Indicator.new(
            'lplayer', 'lplayer', AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        self.indicator.set_menu(self.create_menu())

        self.indicator.set_icon_full(PLAY, _('Play'))
        self.indicator.set_label('', '')
        self.indicator.connect('scroll-event', self.play_or_pause)

    def create_menu(self):
        menu = Gtk.Menu()

        self.current = Gtk.ImageMenuItem.new_with_label(_('Paused'))
        self.current.connect('activate', self.play_or_pause)
        self.current.set_always_show_image(True)
        self.current.show()
        menu.append(self.current)

        separator1 = Gtk.SeparatorMenuItem()
        separator1.show()
        menu.append(separator1)

        self.next = Gtk.ImageMenuItem(label=_('Previous'))
        self.next.show()
        self.next.connect('activate', self.on_activate_previous)
        menu.append(self.next)

        self.previous = Gtk.ImageMenuItem(label=_('Next'))
        self.previous.show()
        self.previous.connect('activate', self.on_activate_next)
        menu.append(self.previous)


        separator2 = Gtk.SeparatorMenuItem()
        separator2.show()
        menu.append(separator2)

        self.show_main_window = Gtk.MenuItem.new_with_label(_('Hide main window'))
        self.show_main_window.show()
        self.show_main_window.connect('activate', self.on_show_main_window)
        menu.append(self.show_main_window)

        ayuda_menu = Gtk.MenuItem(label=_('Help'))
        ayuda_menu.set_submenu(self.get_help_menu())
        ayuda_menu.show()
        menu.append(ayuda_menu)

        separator3 = Gtk.SeparatorMenuItem()
        separator3.show()
        menu.append(separator3)

        exit_option = Gtk.MenuItem.new_with_label(_('Quit'))
        exit_option.show()
        exit_option.connect('activate', self.on_exit_option)
        menu.append(exit_option)


        return menu

    def on_exit_option(self, widget):
        self.main_window._sound_menu_quit()
    
    def on_activate_next(self, widget):
        self.emit('next')
    
    def on_activate_previous(self, widget):
        self.emit('previous')

    def on_show_main_window(self, widget):
        if self.main_window.is_visible():
            self.main_window.hide()
            self.show_main_window.set_label(_('Show main window'))
        else:
            self.main_window.show()
            self.show_main_window.set_label(_('Hide main window'))
    
    def main_window_is_hidden(self):
        self.show_main_window.set_label(_('Show main window'))

    def play(self):
        GLib.idle_add(self.indicator.set_icon_full, PAUSE, _('Pause'))

    def pause(self):
        GLib.idle_add(self.indicator.set_icon_full, PLAY, _('Play'))

    def play_or_pause(self, *_):
        if self.indicator.get_icon() == PLAY:
            self.emit('play')
        else:
            self.emit('pause')

    def set_current(self, label, hash=None):
        self.current.set_label(label)
        if hash is not None:
            filename = os.path.join(
                comun.THUMBNAILS_DIR, '{0}.png'.format(hash))
            if os.path.exists(filename):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    filename, 24, 24)
        if hash is None or pixbuf is None:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    comun.NOIMAGE_ICON, 24, 24)
        self.current.set_image(Gtk.Image.new_from_pixbuf(pixbuf))


    def get_help_menu(self):
        help_menu = Gtk.Menu()
        #
        homepage_item = Gtk.MenuItem(label=_(
            'Homepage'))
        homepage_item.connect('activate',
                              lambda x: webbrowser.open('http://www.atareao.es\
/aplicacion/lplayer/'))
        homepage_item.show()
        help_menu.append(homepage_item)
        #
        help_item = Gtk.MenuItem(label=_(
            'Get help online...'))
        help_item.connect('activate',
                          lambda x: webbrowser.open('http://www.atareao.es\
/aplicacion/lplayer/'))
        help_item.show()
        help_menu.append(help_item)
        #
        translate_item = Gtk.MenuItem(label=_(
            'Translate this application...'))
        translate_item.connect('activate',
                               lambda x: webbrowser.open('https://translations\
.launchpad.net/lplayer'))
        translate_item.show()
        help_menu.append(translate_item)
        #
        bug_item = Gtk.MenuItem(label=_(
            'Report a bug...'))
        bug_item.connect('activate',
                         lambda x: webbrowser.open('https://github.com/atareao\
/lplayer/issues'))
        bug_item.show()
        help_menu.append(bug_item)
        #
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        help_menu.append(separator)
        #
        twitter_item = Gtk.MenuItem(label=_(
            'Follow me in Twitter'))
        twitter_item.connect(
            'activate',
            lambda x: webbrowser.open('https://twitter.com/atareao'))
        twitter_item.show()
        help_menu.append(twitter_item)
        #
        googleplus_item = Gtk.MenuItem(label=_(
            'Follow me in Google+'))
        googleplus_item.connect('activate',
                                lambda x: webbrowser.open(
                                    'https://plus.google.com/\
118214486317320563625/posts'))
        googleplus_item.show()
        help_menu.append(googleplus_item)
        #
        facebook_item = Gtk.MenuItem(label=_(
            'Follow me in Facebook'))
        facebook_item.connect(
            'activate',
            lambda x: webbrowser.open('http://www.facebook.com/elatareao'))
        facebook_item.show()
        help_menu.append(facebook_item)
        #
        about_item = Gtk.MenuItem.new_with_label(_('About'))
        about_item.connect('activate', self.menu_about_response)
        about_item.show()
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        help_menu.append(separator)
        help_menu.append(about_item)
        #
        help_menu.show()
        return help_menu

    def menu_about_response(self, widget):
        self.menu_offon(False)
        widget.set_sensitive(False)
        ad = Gtk.AboutDialog()
        ad.set_name(comun.APPNAME)
        ad.set_version(comun.VERSION)
        ad.set_copyright('Copyrignt (c) 2011-2016\nLorenzo Carbonell')
        ad.set_comments(_('A weather indicator'))
        ad.set_license('''
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
''')
        ad.set_website('http://www.atareao.es')
        ad.set_website_label('http://www.atareao.es')
        ad.set_authors([
            'Pascal De Vuyst <pascal.devuyst@gmail.com>',
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>',
            'doug <https://launchpad.net/~r-d-vaughan>'])
        ad.set_translator_credits('antisa <https://launchpad.net/~antisa>\n\
António Manuel Dias <https://launchpad.net/~ammdias>\n\
Clicksights <https://launchpad.net/~bj7u6139zdyf2a6nz2ly74oec10f2ln-info>\n\
Cooter <https://launchpad.net/~cooter>\n\
Daniel Nylander <https://launchpad.net/~yeager>\n\
Darian Shalev <https://launchpad.net/~lifusion>\n\
DimmuBoy <https://launchpad.net/~dimmuboy>\n\
Emmanuel Brun <https://launchpad.net/~manu57>\n\
Euthymios Spentzos <https://launchpad.net/~voreas>\n\
Gerhard Radatz <https://launchpad.net/~gerhard-radatz>\n\
Grzelny <https://launchpad.net/~grzelny>\n\
Gyaraki László <https://launchpad.net/~gyarakilaszlo>\n\
Hoàng Ngọc Long <https://launchpad.net/~ngoclong19>\n\
Hu Feifei <https://launchpad.net/~gracegreener>\n\
Ibrahim Saed <https://launchpad.net/~ibraheem5000>\n\
Jack H. Daniels <https://launchpad.net/~jack-3wh>\n\
Joseba Oses <https://launchpad.net/~sdsoldi-gmail>\n\
Kim Allamandola <https://launchpad.net/~spacexplorer>\n\
kingdruid <https://launchpad.net/~kingdruid>\n\
Mantas Kriaučiūnas <https://launchpad.net/~mantas>\n\
Maroje Delibasic <https://launchpad.net/~maroje-delibasic>\n\
nehxby <https://launchpad.net/~nehxby-gmail>\n\
Nikola Petković <https://launchpad.net/~nikolja5-gmail>\n\
pardalinux <https://launchpad.net/~pardalinux>\n\
Praveen Illa <https://launchpad.net/~telugulinux>\n\
Radek Šprta <https://launchpad.net/~radek-sprta>\n\
Ricardo <https://launchpad.net/~ragmster>\n\
rodion <https://launchpad.net/~rodion-samusik>\n\
Sal Inski <https://launchpad.net/~syb3ria>\n\
sfc <https://launchpad.net/~sfc-0>\n\
Sohrab <https://launchpad.net/~sohrab-naushad>\n\
Styrmir Magnússon <https://launchpad.net/~styrmirm>\n\
sylinub <https://launchpad.net/~sylinub>\n\
whochismo <https://launchpad.net/~whochismo>\n')
        ad.set_documenters([
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
        ad.set_artists([
            '~mohitg <http://mohitg.deviantart.com/>',
            '~MerlinTheRed <http://merlinthered.deviantart.com/>'])
        ad.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        ad.set_icon(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        ad.set_program_name(comun.APPNAME)
        ad.run()
        ad.destroy()
        widget.set_sensitive(True)
        self.menu_offon(True)

if __name__ == '__main__':
    indicator = Indicator()
    Gtk.main()
