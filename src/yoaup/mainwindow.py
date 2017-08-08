#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# mainwindow.py
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
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Notify
import os
from dbus.mainloop.glib import DBusGMainLoop
from . import comun
from .comun import _
from .sound_menu import SoundMenuControls
from .player import Player
from .player import Status
from .configurator import Configuration
from .listboxrowwithdata import ListBoxRowWithData
from .async import async_function
from .utils import from_remote_image_to_base64
from .utils import get_thumbnail_filename_for_audio
from .youtube_utils import resolve_youtube_url
from .downloadermanager import DownloaderManager
from .showinfodialog import ShowInfoDialog

DEFAULT_CURSOR = Gdk.Cursor(Gdk.CursorType.ARROW)
WAIT_CURSOR = Gdk.Cursor(Gdk.CursorType.WATCH)

CSS = '''
#button:hover,
#button {
    border-image: none;
    background-image: none;
    background-color: rgba(0, 0, 0, 0);
    border-color: rgba(0, 0, 0, 0);
    border-image: none;
    border-radius: 0;
    border-width: 0;
    border-style: solid;
    text-shadow: 0 0 rgba(0, 0, 0, 0);
    box-shadow: 0 0 rgba(0, 0, 0, 0), 0 0 rgba(0, 0, 0, 0);
}
#button:hover{
    background-color: rgba(0, 0, 0, 0.1);
}
'''


def get_index_audio(audios, display_id):
    for index, audio in enumerate(audios):
        if audio['display_id'] == display_id:
            return index
    return -1


class MainWindow(Gtk.ApplicationWindow):
    __gsignals__ = {
        'text-changed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                         (object,)),
        'save-me': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                    (object,)), }

    def __init__(self, app, afile=None):
        Gtk.ApplicationWindow.__init__(self, application=app)

        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)
        self.set_default_size(600, 600)
        self.connect('destroy', self.on_close)

        self.get_root_window().set_cursor(WAIT_CURSOR)

        self.active_row = None
        self.updater = None
        self.configuration = Configuration()

        max_action = Gio.SimpleAction.new_stateful(
            "maximize", None, GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.notification = Notify.Notification.new('', '', None)

        self.player = Player()
        self.player.connect('started', self.on_player_started)
        self.player.connect('paused', self.on_player_paused)
        self.player.connect('stopped', self.on_player_stopped)

        DBusGMainLoop(set_as_default=True)
        self.sound_menu = SoundMenuControls('YOAUP')
        self.sound_menu._sound_menu_is_playing = self._sound_menu_is_playing
        self.sound_menu._sound_menu_play = self._sound_menu_play
        self.sound_menu._sound_menu_pause = self._sound_menu_pause
        self.sound_menu._sound_menu_next = self._sound_menu_next
        self.sound_menu._sound_menu_previous = self._sound_menu_previous
        self.sound_menu._sound_menu_raise = self._sound_menu_raise
        self.sound_menu._sound_menu_stop = self._sound_menu_stop

        # Vertical box. Contains menu and PaneView
        vbox = Gtk.VBox(False, 2)
        self.add(vbox)
        #

        # Init HeaderBar
        self.init_headerbar()

        # Init Menu
        # self.init_menu()

        # Init Toolbar
        # self.init_toolbar()
        #
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        scrolledwindow.set_visible(True)
        vbox.pack_start(scrolledwindow, True, True, 0)

        self.trackview = Gtk.ListBox()
        self.trackview.connect('row-activated', self.on_row_activated)
        self.trackview.connect('row-selected', self.on_row_selected)
        self.trackview.connect('selected-rows-changed',
                               self.on_row_selected_changed)
        self.trackview.set_activate_on_single_click(False)
        self.trackview.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        scrolledwindow.add(self.trackview)

        for index, track in enumerate(self.configuration.get('audios')):
            row = ListBoxRowWithData(track, index)
            row.connect('button_play_pause_clicked', self.on_row_play, row)
            row.connect('button_info_clicked', self.on_row_info, row)
            row.connect('button_listened_clicked', self.on_row_listened, row)
            row.connect('button_download_clicked', self.on_row_download, row)
            row.show()
            self.trackview.add(row)

        self.get_root_window().set_cursor(DEFAULT_CURSOR)

        row = self.trackview.get_row_at_index(0)
        self.trackview.handler_block_by_func(self.on_row_selected)
        self.trackview.select_row(row)
        self.trackview.handler_unblock_by_func(self.on_row_selected)

        self.downloaderManager = DownloaderManager()

        self.load_css()
        self.show_all()
        self.play_controls.set_visible(True)
        if len(self.trackview.get_children()) > 0:
            self.active_row = self.trackview.get_row_at_index(0)

    def on_close(self, widget):
        self.configuration.save()

    def on_maximize_toggle(self, action, value):
            action.set_state(value)
            if value.get_boolean():
                self.maximize()
            else:
                self.unmaximize()

    def on_row_download_started(self, widget, row):
        row.set_downloading(True)

    def on_row_download_ended(self, widget, row):
        row.set_downloading(False)
        filename = os.path.join(comun.AUDIO_DIR,
                                '{0}.ogg'.format(row.audio['display_id']))
        row.set_downloaded(os.path.exists(filename))

    def on_row_download_failed(self, widget, row):
        row.set_downloading(False)
        row.set_downloaded(False)

    def on_row_download(self, widget, row):
        if row.audio['downloaded'] is True:
            filename = os.path.join(comun.AUDIO_DIR,
                                    '{0}.ogg'.format(row.audio['display_id']))
            if os.path.exists(filename):
                row.set_downloaded(False)
        else:
            self.downloaderManager.add(row)
            self.downloaderManager.connect('started',
                                           self.on_row_download_started)
            self.downloaderManager.connect('ended',
                                           self.on_row_download_ended)
            self.downloaderManager.connect('failed',
                                           self.on_row_download_failed)

    def on_row_listened(self, widget, row):
        listened = not row.audio['listened']
        row.set_listened(listened)
        self.set_audio(row.audio)

    def on_row_info(self, widget, row):
        sid = ShowInfoDialog(self,
                             row.audio['creator'],
                             row.audio['title'],
                             row.audio['url'],
                             row.audio['description'])
        sid.run()
        sid.hide()
        sid.destroy()

    def on_row_play(self, widget, row):
        if self.active_row is not None and self.active_row != row and\
                self.active_row.is_playing is True:
            self.active_row.set_playing(False)
            self.player.pause()
            self.control['play-pause'].get_child().set_from_gicon(
                Gio.ThemedIcon(name='media-playback-start-symbolic'),
                Gtk.IconSize.BUTTON)
            self.control['play-pause'].set_tooltip_text(_('Play'))
        self.active_row = row
        if self.active_row.is_playing is False:
            filename = os.path.join(comun.AUDIO_DIR,
                                    '{0}.ogg'.format(row.audio['display_id']))

            self.player.set_filename(filename)
            self.player.set_speed(self.configuration.get('speed'))
            self.player.set_remove_silence(
                self.configuration.get('remove_silence'))
            self.player.set_equalizaer(self.configuration.get('equalizer'))

            fraction = float(self.active_row.get_position())
            self.control['position'].handler_block_by_func(
                self.on_position_button_changed)
            self.control['position'].set_value(fraction)
            self.control['label-position'].set_text(
                _('Position') + ': {0}%'.format(int(fraction * 100)))
            self.control['position'].handler_unblock_by_func(
                self.on_position_button_changed)
            self.control['play-pause'].get_child().set_from_gicon(
                Gio.ThemedIcon(name='media-playback-pause-symbolic'),
                Gtk.IconSize.BUTTON)
            self.control['play-pause'].set_tooltip_text(_('Pause'))
            if self.active_row.get_position() > 0:
                self.player.set_position(
                    self.active_row.audio['position'] *
                    float(self.active_row.audio['duration']))
            artists = ['']
            album = self.active_row.audio['title']
            title = self.active_row.audio['title']
            album_art = 'file://' + get_thumbnail_filename_for_audio(
                self.active_row.audio)
            self.sound_menu.song_changed(artists, album, title, album_art)
            self.sound_menu.signal_playing()

            self.notification.update('{0} - {1}'.format(
                'YOAUP',
                album),
                title,
                album_art)
            self.notification.show()

            if self.active_row.audio['position'] > 0 and\
                    self.active_row.audio['position'] <= 1:
                self.player.set_position(
                    self.active_row.audio['position'] *
                    float(self.active_row.audio['duration']))
            self.player.play()
            self.updater = GLib.timeout_add_seconds(1, self.update_position)
            self.active_row.set_playing(True)
        else:
            artists = [self.active_row.audio['creator']]
            album = self.active_row.audio['title']
            title = self.active_row.audio['title']
            album_art = 'file://' + get_thumbnail_filename_for_audio(
                self.active_row.audio)
            self.sound_menu.song_changed(artists, album, title, album_art)
            self.sound_menu.signal_paused()

            self.player.pause()
            self.control['play-pause'].get_child().set_from_gicon(
                Gio.ThemedIcon(name='media-playback-start-symbolic'),
                Gtk.IconSize.BUTTON)
            self.control['play-pause'].set_tooltip_text(_('Play'))

            self.active_row.set_playing(False)
            audios = self.configuration.get('audios')
            audio_index = get_index_audio(
                audios, self.active_row.audio['display_id'])
            audios[audio_index]['position'] = self.active_row.audio['position']
            self.configuration.set('audios', audios)

    def _sound_menu_is_playing(self):
        return self.player.status == Status.PLAYING

    def _sound_menu_play(self, *args):
        """Play"""
        # self.is_playing = True  # Need to overwrite
        row = self.active_row
        if row is None:
            row = self.trackview.get_row_at_index(0)
            self.active_row = row
        self.active_row.click_button_play()

    def _sound_menu_stop(self):
        """Pause"""
        exit(0)
        if self.active_row is not None and self.active_row.is_playing is True:
            self.active_row.click_button_play()

    def _sound_menu_pause(self, *args):
        """Pause"""
        if self.active_row is not None:
            self.active_row.click_button_play()

    def _sound_menu_next(self, *args):
        """Next"""
        index = self.get_next_playable_track()
        if index is not None:
            row = self.trackview.get_row_at_index(index)
            row.click_button_play()

    def _sound_menu_previous(self, *args):
        """Previous"""
        index = self.get_previous_playable_track()
        if index is not None:
            row = self.trackview.get_row_at_index(index)
            row.click_button_play()

    def _sound_menu_raise(self):
        """Click on player"""
        self.show()

    def on_row_selected(self, widget, row):
        pass

    def get_playable_tracks(self):
        playables = []
        for index in range(0, len(self.trackview.get_children())):
            if self.trackview.get_row_at_index(index).can_play():
                playables.append(index)
        return sorted(playables)

    def get_next_playable_track(self):
        playables = self.get_playable_tracks()
        if len(playables) > 0:
            if self.active_row is not None and\
                    self.active_row.index in playables:
                selected = playables.index(self.active_row.index)
                next = selected + 1
                if next >= len(playables):
                    next = 0
                return playables[next]
            else:
                return playables[0]
        return None

    def get_previous_playable_track(self):
        playables = self.get_playable_tracks()
        if len(playables) > 0:
            if self.active_row is not None and\
                    self.active_row.index in playables:
                selected = playables.index(self.active_row.index)
                previous = selected - 1
                if previous < 0:
                    previous = len(playables) - 1
                return playables[previous]
            else:
                return playables[0]
        return None

    def set_audio(self, audio):
        audios = self.configuration.get('audios')
        for index, audio in enumerate(audios):
            if audio['display_id'] == audio['display_id']:
                audios[index] = audio
                self.configuration.set('audios', audios)
                break

    def update_position(self):
        if self.active_row is not None:
            if self.active_row.audio['duration'] == 0:
                try:
                    duration = self.player.get_duration()
                    if duration > 0:
                        self.active_row.set_duration(duration)
                        self.set_audio(self.active_row.audio)
                except Exception as e:
                    print(e)
            position = self.player.get_position() / float(
                self.active_row.audio['duration'])
            if position >= 0:
                self.active_row.set_position(position)
                try:
                    duration = self.player.get_duration()
                    if duration > 0:
                        self.active_row.set_duration(duration)
                except Exception as e:
                    print(e)
                self.set_audio(self.active_row.audio)

                self.control['position'].handler_block_by_func(
                    self.on_position_button_changed)
                self.control['position'].set_value(int(position * 100))
                self.control['label-position'].set_text(
                    _('Position') + ': {0}%'.format(int(position * 100)))
                self.control['position'].handler_unblock_by_func(
                    self.on_position_button_changed)
                if position >= 0.99:
                    self.active_row.set_listened(True)
                    self.active_row.set_position(0)
                    if self.configuration.get('remove_on_listened') is True:
                        self.active_row.set_downloaded(False)
                    self.set_audio(self.active_row.audio)
                    if self.active_row.is_playing is True:
                        self.active_row.set_playing(False)
                        self.player.pause()
                    self._sound_menu_next()
            return self.player.status == Status.PLAYING

    def on_player_started(self, player, position):
        pass

    def on_player_paused(self, player, position):
        pass

    def on_player_stopped(self, player, position):
        pass

    def on_row_selected_changed(self, widget):

        pass

    def on_row_activated(self, widget, row):
        self.active_row = row
        self.trackview.select_row(row)

    def on_downloader_failed(self, widget, row, filename):
        if os.path.exists(filename):
            os.remove(filename)
        row.set_downloading(False)
        row.set_downloaded(False)

        self.control['play-pause'].set_sensitive(False)
        self.control['speed'].set_sensitive(False)
        self.control['position'].set_sensitive(False)

        self.get_root_window().set_cursor(DEFAULT_CURSOR)

    def on_downloader_ended(self, widget, row, filename):
        if os.path.exists(filename):
            filename = filename.split('/')[-1]

            # self.db.set_track_downloaded(row.data['id'], filename)
            # self.configuration.get('audios')
            row.set_downloading(False)
            row.set_downloaded(True)

            self.control['play-pause'].set_sensitive(True)
            self.control['speed'].set_sensitive(True)
            self.control['position'].set_sensitive(True)

        self.set_audio(row.audio)

        self.get_root_window().set_cursor(DEFAULT_CURSOR)

    def on_play_continuously_changed(self, widget, value):
        self.configuration.set('play_continuously', widget.get_active())

    def on_remove_silence_changed(self, widget, value):
        self.player.set_remove_silence(widget.get_active())
        self.configuration.set('remove_silence', widget.get_active())

    def on_speed_button_changed(self, widget):
        value = widget.get_value()
        self.control['label-speed'].set_text(
            _('Speed') + ': {0}x'.format(int(value * 10) / 10))
        self.player.set_speed(value)
        self.configuration.set('speed', value)

    def on_position_button_changed(self, widget):
        value = widget.get_value()

        self.control['label-position'].set_label(
            _('Position' + ': {0}%'.format(int(value))))
        if self.active_row is not None:
            value = float(value) / 100.0
            if value >= 0.0 and value <= 1.0:
                self.active_row.set_position(value)
                self.set_audio(self.active_row.audio)
                self.player.set_position(
                    value * float(self.active_row.audio['duration']))

    def init_headerbar(self):
        self.control = {}
        self.menu_selected = 'suscriptions'
        #
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = comun.APPNAME
        self.set_titlebar(hb)

        self.play_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        hb.pack_start(self.play_controls)

        popover = Gtk.Popover()
        popover_grid = Gtk.Grid()
        popover_grid.set_margin_top(10)
        popover_grid.set_margin_bottom(10)
        popover_grid.set_margin_left(10)
        popover_grid.set_margin_right(10)
        popover_grid.set_column_spacing(5)
        popover_grid.set_row_spacing(5)
        popover.add(popover_grid)

        self.control['label-position'] = Gtk.Label(_('Position') + ':')
        self.control['label-position'].set_alignment(0, 0.5)
        popover_grid.attach(self.control['label-position'], 0, 0, 5, 1)
        self.control['position'] = Gtk.Scale()
        self.control['position'].set_tooltip_text(
            _('Relative position'))
        self.control['position'].set_adjustment(
            Gtk.Adjustment(0, 0, 100, 1, 1, 5))
        self.control['position'].connect('value-changed',
                                         self.on_position_button_changed)
        self.control['position'].set_value(0)
        popover_grid.attach(self.control['position'], 5, 0, 5, 1)

        self.control['label-speed'] = Gtk.Label(_('Speed') + ':')
        self.control['label-speed'].set_alignment(0, 0.5)
        popover_grid.attach(self.control['label-speed'], 0, 1, 5, 1)
        self.control['speed'] = Gtk.Scale()
        self.control['speed'].set_adjustment(Gtk.Adjustment(
            1, 0.5, 4, 0.1, 0.1, 1))
        self.control['speed'].set_size_request(200, 0)
        self.control['speed'].connect('value-changed',
                                      self.on_speed_button_changed)
        self.control['speed'].set_value(self.configuration.get('speed'))
        popover_grid.attach(self.control['speed'], 5, 1, 5, 1)

        label = Gtk.Label(_('Remove silence') + ':')
        label.set_alignment(0, 0.5)
        popover_grid.attach(label, 0, 2, 5, 1)

        self.control['remove-silence'] = Gtk.Switch()
        self.control['remove-silence'].set_active(
            self.configuration.get('remove_silence'))
        self.control['remove-silence'].connect(
            'notify::active', self.on_remove_silence_changed)
        tbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        tbox.add(self.control['remove-silence'])
        popover_grid.attach(tbox, 5, 2, 5, 1)

        label = Gtk.Label(_('Play continuously') + ':')
        label.set_alignment(0, 0.5)
        popover_grid.attach(label, 0, 3, 5, 1)

        self.control['play_continuously'] = Gtk.Switch()
        self.control['play_continuously'].set_active(
            self.configuration.get('play_continuously'))
        self.control['play_continuously'].connect(
            'notify::active', self.on_play_continuously_changed)
        tbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        tbox.add(self.control['play_continuously'])
        popover_grid.attach(tbox, 5, 3, 5, 1)

        popover_grid.attach(Gtk.Label(_('Equalizer')), 0, 4, 10, 1)

        for index in range(0, 10):
            band = 'band{0}'.format(index)
            self.control[band] = Gtk.Scale.new_with_range(
                Gtk.Orientation.VERTICAL, -24.0, 12.0, 0.1)
            self.control[band].set_size_request(0, 200)
            self.control[band].set_value(
                self.configuration.get('equalizer')[band])
            self.control[band].connect('value-changed',
                                       self.on_band_changed, band)
            popover_grid.attach(self.control[band], index, 5, 1, 1)

        popover_grid.show_all()

        self.control['configuration'] = Gtk.MenuButton()
        self.control['configuration'].set_tooltip_text(_('Configuration'))
        self.control['configuration'].add(
            Gtk.Image.new_from_gicon(Gio.ThemedIcon(
                name='preferences-system-symbolic'), Gtk.IconSize.BUTTON))
        self.control['configuration'].set_popover(popover)
        self.play_controls.pack_start(self.control['configuration'],
                                      False, False, 0)

        self.control['previous'] = Gtk.Button()
        self.control['previous'].set_tooltip_text(_('Previous'))
        self.control['previous'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='go-next-symbolic-rtl'), Gtk.IconSize.BUTTON))
        self.control['previous'].connect('clicked',
                                         self._sound_menu_previous)
        self.play_controls.pack_start(self.control['previous'],
                                      False, False, 0)

        self.control['play-pause'] = Gtk.Button()
        self.control['play-pause'].set_tooltip_text(_('Play'))
        self.control['play-pause'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='media-playback-start-symbolic'), Gtk.IconSize.BUTTON))
        self.control['play-pause'].connect('clicked',
                                           self._sound_menu_play)
        self.play_controls.pack_start(self.control['play-pause'],
                                      False, False, 0)

        self.control['next'] = Gtk.Button()
        self.control['next'].set_tooltip_text(_('Next'))
        self.control['next'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='go-next-symbolic'), Gtk.IconSize.BUTTON))
        self.control['next'].connect('clicked',
                                     self._sound_menu_next)
        self.play_controls.pack_start(self.control['next'], False, False, 0)

        help_model = Gio.Menu()

        help_section0_model = Gio.Menu()
        help_section0_model.append(_('Preferences'), 'app.set_preferences')
        help_section0 = Gio.MenuItem.new_section(None, help_section0_model)
        help_model.append_item(help_section0)

        help_section1_model = Gio.Menu()
        help_section1_model.append(_('Homepage'), 'app.goto_homepage')
        help_section1 = Gio.MenuItem.new_section(None, help_section1_model)
        help_model.append_item(help_section1)

        help_section2_model = Gio.Menu()
        help_section2_model.append(_('Code'), 'app.goto_code')
        help_section2_model.append(_('Issues'), 'app.goto_bug')
        help_section2 = Gio.MenuItem.new_section(None, help_section2_model)
        help_model.append_item(help_section2)

        help_section3_model = Gio.Menu()
        help_section3_model.append(_('Twitter'), 'app.goto_twitter')
        help_section3_model.append(_('Facebook'), 'app.goto_facebook')
        help_section3_model.append(_('Google+'), 'app.goto_google_plus')
        help_section3 = Gio.MenuItem.new_section(None, help_section3_model)
        help_model.append_item(help_section3)

        help_section4_model = Gio.Menu()
        help_section4_model.append(_('Donations'), 'app.goto_donate')
        help_section4 = Gio.MenuItem.new_section(None, help_section4_model)
        help_model.append_item(help_section4)

        help_section5_model = Gio.Menu()
        help_section5_model.append(_('About'), 'app.about')
        help_section5 = Gio.MenuItem.new_section(None, help_section5_model)
        help_model.append_item(help_section5)

        self.control['help'] = Gtk.MenuButton()
        self.control['help'].set_menu_model(help_model)
        self.control['help'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='open-menu-symbolic'), Gtk.IconSize.BUTTON))
        hb.pack_end(self.control['help'])

        self.control['remove'] = Gtk.Button()
        self.control['remove'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='list-remove-symbolic'), Gtk.IconSize.BUTTON))
        self.control['remove'].connect('clicked', self.on_remove_track)
        hb.pack_end(self.control['remove'])

        self.popover_add = Gtk.Popover()
        popover_add_grid = Gtk.Grid()
        self.popover_add.add(popover_add_grid)
        popover_add_grid.attach(Gtk.Label(_('YouTube url') + ':'),
                                0, 0, 1, 1)
        self.control['add_entry'] = Gtk.SearchEntry()
        self.control['add_entry'].connect('activate',
                                          self.on_add_entry_clicked)
        popover_add_grid.attach(self.control['add_entry'], 1, 0, 1, 1)
        popover_add_grid.show_all()
        # popover_add.show_all()

        self.control['add'] = Gtk.MenuButton()
        self.control['add'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='list-add-symbolic'), Gtk.IconSize.BUTTON))
        self.control['add'].set_popover(self.popover_add)
        hb.pack_end(self.control['add'])

    def on_band_changed(self, widget, band):
        equalizer = self.configuration.get('equalizer')
        equalizer[band] = widget.get_value()
        self.configuration.set('equalizer', equalizer)
        self.player.set_equalizer_by_band(int(band[4:]), widget.get_value())
        print(widget, band, int(band[4:]))

    def on_add_entry_clicked(self, widget):
        text = widget.get_text()
        self.add_track(text)
        widget.get_buffer().delete_text(0, -1)
        self.popover_add.hide()

    def on_remove_track(self, widget):
        if self.active_row is not None:
            if len(self.trackview.get_selected_rows()) > 1:
                msg = _('Are you sure to delete the tracks')
            else:
                msg = _('Are you sure to delete the track')
            dialog = Gtk.MessageDialog(
                self,
                0,
                Gtk.MessageType.WARNING,
                Gtk.ButtonsType.OK_CANCEL,
                msg)
            if dialog.run() == Gtk.ResponseType.OK:
                dialog.destroy()
                audios = self.configuration.get('audios')
                for row in self.trackview.get_selected_rows():
                    audios.remove(row.audio)
                    self.configuration.set('audios', audios)
                    self.trackview.remove(row)
                    extension = row.audio['ext']
                    audio_id = row.audio['display_id']
                    filein = os.path.join(
                        comun.AUDIO_DIR,
                        '{0}.{1}'.format(audio_id, extension))
                    fileout = os.path.join(
                        comun.AUDIO_DIR,
                        '{0}.{1}'.format(audio_id, 'ogg'))
                    if os.path.exists(filein):
                        os.remove(filein)
                    if os.path.exists(fileout):
                        os.remove(fileout)
                    self.trackview.show_all()
                    if self.active_row.audio == row.audio and\
                            len(self.trackview.get_children()) > 0:
                        self.active_row = self.trackview.get_row_at_index(0)
                    else:
                        self.active_row = None
            else:
                dialog.destroy()

    def add_track(self, text):

        def on_add_track_in_thread_done(result, error):
            if error is None and result is not None:
                audios = self.configuration.get('audios')
                for audio in audios:
                    if audio == result:
                        return
                audios.append(result)
                self.configuration.set('audios', audios)
                row = ListBoxRowWithData(result, len(audios) - 1)
                row.connect('button_play_pause_clicked',
                            self.on_row_play,
                            row)
                row.connect('button_info_clicked', self.on_row_info, row)
                row.connect('button_listened_clicked',
                            self.on_row_listened,
                            row)
                row.connect('button_download_clicked',
                            self.on_row_download,
                            row)
                row.show()
                self.trackview.prepend(row)
                self.trackview.show_all()

                self.configuration.set('audios', audios)
                self.configuration.save()
                if self.configuration.get('download_on_added') is True:
                    self.on_row_download(None, row)

            self.get_root_window().set_cursor(DEFAULT_CURSOR)

        @async_function(on_done=on_add_track_in_thread_done)
        def do_add_track_in_thread(text):
            result = resolve_youtube_url(text)
            if result is not None:
                for audio in self.configuration.get('audios'):
                    if result == audio:
                        return None
                if result['thumbnail'] is not None:
                    thumbnail_base64 = from_remote_image_to_base64(
                        result['thumbnail'])
                    if thumbnail_base64 is not None:
                        result['thumbnail_base64'] = thumbnail_base64
            return result

        self.get_root_window().set_cursor(WAIT_CURSOR)
        do_add_track_in_thread(text)

    def on_toggled(self, widget, arg):
        if widget.get_active() is True:
            if arg == self.menu_selected:
                if self.menu[arg].get_active() is False:
                    self.menu[arg].set_active(True)
            else:
                old = self.menu_selected
                self.menu_selected = arg
                self.menu[old].set_active(False)
        else:
            if self.menu_selected == arg:
                widget.set_active(True)

    def load_css(self):
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER)
