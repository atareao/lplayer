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
    gi.require_version('Gdk', '3.0')
    gi.require_version('Gio', '2.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
    gi.require_version('GdkPixbuf', '2.0')
    gi.require_version('Notify', '0.7')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Notify
import sys
import webbrowser
from .mainwindow import MainWindow
from . import comun
from .comun import _


class MainApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id='es.atareao.lplayer',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.license_type = Gtk.License.GPL_3_0
        self.win = None
        self.new_tracks = []

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

    def on_quit(self, widget, data):
        self.quit()

    def do_command_line(self, command_line):
        if command_line is not None:
            print(command_line.get_arguments(), self.win)
            if len(command_line.get_arguments()) > 1:
                self.new_tracks.extend(command_line.get_arguments()[1:])
        self.do_activate()
        return 0

    def do_startup(self):
        print('do_startup')
        Gtk.Application.do_startup(self)

        def create_action(name,
                          callback=self.action_clicked,
                          var_type=None,
                          value=None):
            if var_type is None:
                action = Gio.SimpleAction.new(name, None)
            else:
                action = Gio.SimpleAction.new_stateful(
                    name,
                    GLib.VariantType.new(var_type),
                    GLib.Variant(var_type, value)
                )
            action.connect('activate', callback)
            return action

        self.add_action(create_action("quit", callback=lambda *_: self.quit()))

        self.set_accels_for_action('app.add', ['<Ctrl>A'])
        self.set_accels_for_action('app.open', ['<Ctrl>O'])
        self.set_accels_for_action('app.quit', ['<Ctrl>Q'])
        self.set_accels_for_action('app.about', ['<Ctrl>F'])

        self.set_accels_for_action('app.play', ['Up'])
        self.set_accels_for_action('app.pause', ['Down'])
        self.set_accels_for_action('app.previous', ['Left'])
        self.set_accels_for_action('app.next', ['Right'])

        self.add_action(create_action(
            'new',
            callback=self.on_headbar_clicked))
        self.add_action(create_action(
            'open',
            callback=self.on_headbar_clicked))
        self.add_action(create_action(
            'close',
            callback=self.on_headbar_clicked))
        self.add_action(create_action(
            'save',
            callback=self.on_headbar_clicked))
        self.add_action(create_action(
            'save_as',
            callback=self.on_headbar_clicked))
        '''s
        self.add_action(create_action(
            'download_all',
            callback=self.on_download_all_clicked))
        '''
        self.add_action(create_action(
            'set_preferences',
            callback=self.on_preferences_clicked))
        self.add_action(create_action(
            'goto_homepage',
            callback=lambda x, y: webbrowser.open(
                'http://www.atareao.es/aplicacion/lplayer')))
        self.add_action(create_action(
            'goto_code',
            callback=lambda x, y: webbrowser.open(
                'https://github.com/atareao/lplayer')))
        self.add_action(create_action(
            'goto_bug',
            callback=lambda x, y: webbrowser.open(
                'https://github.com/atareao/lplayer/issues')))
        self.add_action(create_action(
            'goto_sugestion',
            callback=lambda x, y: webbrowser.open(
                'https://blueprints.launchpad.net/lplayer')))
        self.add_action(create_action(
            'goto_translation',
            callback=lambda x, y: webbrowser.open(
                'https://translations.launchpad.net/lplayer')))
        self.add_action(create_action(
            'goto_questions',
            callback=lambda x, y: webbrowser.open(
                'https://answers.launchpad.net/lplayer')))
        self.add_action(create_action(
            'goto_twitter',
            callback=lambda x, y: webbrowser.open(
                'https://twitter.com/atareao')))
        self.add_action(create_action(
            'goto_google_plus',
            callback=lambda x, y: webbrowser.open(
                'https://plus.google.com/\
118214486317320563625/posts')))
        self.add_action(create_action(
            'goto_facebook',
            callback=lambda x, y: webbrowser.open(
                'http://www.facebook.com/elatareao')))
        self.add_action(create_action(
            'goto_donate',
            callback=lambda x, y: webbrowser.open(
                'https://www.atareao.es/donar/')))
        self.add_action(create_action(
            'about',
            callback=self.on_about_activate))
        self.add_action(create_action(
            'quit',
            callback=self.on_quit_activate))
        self.add_action(create_action(
            'none',
            callback=self.do_none))
        self.add_action(create_action(
            'play',
            callback=self.on_play_activate))
        self.add_action(create_action(
            'pause',
            callback=self.on_pause_activate))
        self.add_action(create_action(
            'previous',
            callback=self.on_previous_activate))
        self.add_action(create_action(
            'next',
            callback=self.on_next_activate))

        action_toggle = Gio.SimpleAction.new_stateful(
            "toggle", None, GLib.Variant.new_boolean(False))
        action_toggle.connect("change-state", self.toggle_toggled)
        self.add_action(action_toggle)

        lbl_variant = GLib.Variant.new_string("h3")
        new_action = Gio.SimpleAction.new_stateful("new",
                                                   lbl_variant.get_type(),
                                                   lbl_variant)
        new_action.connect("activate", self.activate_radio)
        new_action.connect("change-state", self.toggle_heading)
        self.add_action(new_action)

        action_heading = Gio.SimpleAction.new_stateful(
            "heading",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "h1"))
        action_heading.connect("activate", self.activate_radio)
        action_heading.connect("change-state", self.toggle_heading)
        self.add_action(action_heading)

    def activate_radio(self, widget, action, parameter=None):
        self.win.menu['lists'].set_label(action.get_string())
        widget.set_state(action)

    def heading(self, action):
        print(action)

    def toggle_heading(self, action, state):
        print(action, state)

    def do_activate(self):
        print('do_activate')
        if self.win is None:
            self.win = MainWindow(self)
            self.win.show_all()
        self.add_window(self.win)
        self.win.present()
        if len(self.new_tracks) > 0:
            self.win.add_tracks_in_background(self.new_tracks)
            self.new_tracks = []

    def action_clicked(self, action, variant):
        print(action, variant)
        if variant:
            action.set_state(variant)

    def on_headbar_clicked(self, action, optional):
        self.win.on_toolbar_clicked(action, action.get_name())

    def on_support_clicked(self, widget, optional):
        pass

    def on_preferences_clicked(self, action, optional):
        self.win.on_preferences_clicked(None)

    def on_download_all_clicked(self, action, optional):
        self.win.on_download_all_clicked(None)

    def on_quit_activate(self, widget, optional):
        self.win._sound_menu_quit()

    def on_play_activate(self, widget, optional):
        self.win._sound_menu_play()

    def on_pause_activate(self, widget, optional):
        self.win._sound_menu_pause()

    def on_previous_activate(self, widget, optional):
        self.win._sound_menu_previous()

    def on_next_activate(self, widget, optional):
        self.win._sound_menu_next()


    def on_about_activate(self, widget, optional):
        ad = Gtk.AboutDialog(comun.APPNAME, self.win)
        ad.set_name(comun.APPNAME)
        ad.set_version(comun.VERSION)
        ad.set_copyright('Copyrignt (c) 2018-2019\nLorenzo Carbonell')
        ad.set_comments(_('A minimal audio player for Linux'))
        ad.set_license('''
MIT License

Copyright (c) 2012-2018 Lorenzo Carbonell Cerezo <a.k.a. atareao>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')
        ad.set_website('http://www.atareao.es')
        ad.set_website_label('http://www.atareao.es')
        ad.set_authors([
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
        ad.set_documenters([
            'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
        ad.set_translator_credits('\
Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>\n')
        ad.set_program_name(comun.APPNAME)
        ad.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
        ad.run()
        ad.destroy()

    def do_none(self, *args):
        pass

    def toggle_toggled(self, action, state):
            action.set_state(state)
            Gtk.Settings.get_default().set_property(
                "gtk-application-prefer-dark-theme", state)


def main(args):
    Notify.init('lplayer')
    app = MainApplication()
    app.run(args)


if __name__ == "__main__":
    main(sys.argv)
