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
from gi.repository import GdkPixbuf
from gi.repository import Notify
import os
import json
import mimetypes
import urllib
from dbus.mainloop.glib import DBusGMainLoop
from . import comun
from .comun import _
from .sound_menu import SoundMenuControls
from .player import Player
from .player import Status
from .configurator import Configuration
from .listboxrowwithdata import ListBoxRowWithData
from .audio import Audio
from .async import async_function
from .utils import get_thumbnail_filename_for_audio
from .utils import get_pixbuf_from_base64string
from .showinfodialog import ShowInfoDialog
from .preferencesdialog import PreferencesDialog

ALLOWED_MIMETYPES = ['application/x-ogg', 'application/ogg',
                     'audio/x-vorbis+ogg', 'audio/x-scpls', 'audio/x-mp3',
                     'audio/x-mpeg', 'audio/mpeg', 'audio/x-mpegurl']

DEFAULT_CURSOR = Gdk.Cursor(Gdk.CursorType.ARROW)
WAIT_CURSOR = Gdk.Cursor(Gdk.CursorType.WATCH)

CSS = '''
#label:hover,
#label{
    color: rgba(1, 1, 1, 1);
}
#label:selected{
    color: rgba(0, 1, 0, 1);
}
#progressbar,
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


def get_index_audio(audios, hash):
    for index, audio in enumerate(audios):
        if audio['hash'] == hash:
            return index
    return -1


class MainWindow(Gtk.ApplicationWindow):
    __gsignals__ = {
        'text-changed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                         (object,)),
        'save-me': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                    (object,)), }

    def __init__(self, app, files=[]):
        Gtk.ApplicationWindow.__init__(self, application=app)

        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_icon_from_file(comun.ICON)
        self.set_default_size(500, 600)
        self.connect('destroy', self.on_close)

        self.connect('delete_event', self.delete_event)

        self.get_root_window().set_cursor(WAIT_CURSOR)

        self.active_row = None
        self.selected_row = None
        self.is_playing = False
        self.updater = None
        self.configuration = Configuration()
        self.row = self.configuration.get('row')

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
        self.sound_menu = SoundMenuControls('lplayer')
        self.sound_menu._sound_menu_is_playing = self._sound_menu_is_playing
        self.sound_menu._sound_menu_play = self._sound_menu_play
        self.sound_menu._sound_menu_pause = self._sound_menu_pause
        self.sound_menu._sound_menu_next = self._sound_menu_next
        self.sound_menu._sound_menu_previous = self._sound_menu_previous
        self.sound_menu._sound_menu_raise = self._sound_menu_raise
        self.sound_menu._sound_menu_stop = self._sound_menu_stop
        self.sound_menu._sound_menu_quit = self._sound_menu_quit

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
        self.trackview.connect('button-press-event', self.on_clicked)
        self.trackview.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        scrolledwindow.add(self.trackview)

        for index, track in enumerate(self.configuration.get('audios')):
            row = ListBoxRowWithData(track, index)
            row.connect('button_info_clicked', self.on_row_info, row)
            row.connect('button_listened_clicked', self.on_row_listened, row)
            row.show()
            self.trackview.add(row)

        self.get_root_window().set_cursor(DEFAULT_CURSOR)

        row = self.trackview.get_row_at_index(0)
        self.trackview.handler_block_by_func(self.on_row_selected)
        self.trackview.select_row(row)
        self.trackview.handler_unblock_by_func(self.on_row_selected)

        self.trackview.connect('drag-begin', self.drag_begin)
        self.trackview.connect('drag-data-get', self.drag_data_get_data)
        self.trackview.connect('drag-drop', self.drag_drop)
        self.trackview.connect('drag-data-delete', self.drag_data_delete)
        self.trackview.connect('drag-end', self.drag_end)
        self.trackview.connect('drag-data-received', self.drag_data_received)
        #
        dnd_list = [Gtk.TargetEntry.new('text/plain',
                                        Gtk.TargetFlags.SAME_WIDGET,
                                        1001)]
        self.trackview.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                                       dnd_list,
                                       Gdk.DragAction.MOVE)
        dnd_list = [Gtk.TargetEntry.new('text/plain',
                                        Gtk.TargetFlags.SAME_WIDGET,
                                        1001),
                    Gtk.TargetEntry.new('text/uri-list',
                                        Gtk.TargetFlags.OTHER_APP,
                                        0)]
        self.trackview.drag_dest_set(Gtk.DestDefaults.MOTION |
                                     Gtk.DestDefaults.HIGHLIGHT |
                                     Gtk.DestDefaults.DROP,
                                     dnd_list,
                                     Gdk.DragAction.MOVE)

        self.load_css()
        self.show_all()
        self.play_controls.set_visible(True)
        self.play_controls.grab_focus()
        self.trackview.unselect_all()
        if len(self.trackview.get_children()) > 0:
            if self.row > -1 and self.row < len(self.trackview.get_children()):
                self.trackview.select_row(
                    self.trackview.get_row_at_index(self.row))
                self.set_active_row(self.trackview.get_row_at_index(self.row))
            else:
                self.trackview.select_row(self.trackview.get_row_at_index(0))
                self.set_active_row(self.trackview.get_row_at_index(0))
        self.control['play-pause'].grab_focus()
        if len(files) > 0:
            self.add_tracks_sync(files)

    def drag_drop(self, widget, context, selection, info, time):
        print('==== Drag drop ====')

    def drag_end(self, widget, context):
        print('==== Drag end ====')

    def drag_data_delete(self, widget, context):
        print('==== Drag data delete ====')

    def drag_begin(self, widget, context):
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        print('==== Drag begin ====')
        rows = self.trackview.get_selected_rows()
        if len(rows) > 0:
            selected = rows[0]
            pixbuf = get_pixbuf_from_base64string(
                selected.audio['thumbnail_base64']).scale_simple(
                64, 64, GdkPixbuf.InterpType.BILINEAR)
            Gtk.drag_set_icon_pixbuf(context, pixbuf, -2, -2)

    def drag_data_get_data(self, treeview, context, selection, target_id,
                           etime):
        print('==== Drag get data ====')
        print(target_id)
        if target_id == 1001:
            items = self.trackview.get_selected_rows()
            if len(items) > 0:
                rows = []
                for item in items:
                    rows.append(item.index)
                data = json.dumps(rows)
                selection.set_text(data, len(data))
        else:
            print(context)

    def drag_data_received(self, widget, drag_context, x, y, selection_data,
                           info, timestamp):
        print('==== Drag received data ====')
        if info == 1001:
            row_after = self.trackview.get_row_at_y(y)
            print(row_after.audio['title'])
            rows = json.loads(selection_data.get_text())
            rows_to_move = []
            for row in rows:
                rows_to_move.append(self.trackview.get_row_at_index(row))
            for row_to_move in rows_to_move:
                print(row_to_move.audio['title'])
                self.trackview.remove(row_to_move)
            index_row_after = self.get_index_for_audio(row_after.audio)
            for index, row_to_move in enumerate(rows_to_move):
                print(index_row_after, index)
                new_row = ListBoxRowWithData(row_to_move.audio,
                                             index_row_after + index)
                new_row.connect('button_info_clicked',
                                self.on_row_info, new_row)
                new_row.connect('button_listened_clicked',
                                self.on_row_listened,
                                new_row)
                self.trackview.insert(new_row,
                                      index_row_after + index)
            self.trackview.show_all()
            self.update_audios()
        else:
            print('aqui')
            filenames = selection_data.get_uris()
            print(filenames)
            tracks_to_add = []
            for filename in filenames:
                if len(filename) > 8:
                    filename = urllib.request.url2pathname(filename)
                    filename = filename[7:]
                    if os.path.exists(filename):
                        mime = mimetypes.guess_type(filename)[0]
                        if mime in ALLOWED_MIMETYPES:
                            tracks_to_add.append(filename)
            if len(tracks_to_add) > 0:
                print(tracks_to_add)
                # self.add_tracks(tracks_to_add)
                self.add_tracks_sync(tracks_to_add)
                return True
        return False

    def on_clicked(self, widget, event):
        print('clicked')
        if event.button == 1 and\
                event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            if self.selected_row is not None:
                self.play_row(self.selected_row)
        if event.get_state() & Gdk.ModifierType.SHIFT_MASK or\
                event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            pass
        else:
            self.trackview.unselect_all()
        self.trackview.select_row(self.trackview.get_row_at_y(event.y))

    def delete_event(self, widget, arg):
        self.hide()
        return True

    def on_close(self, widget):
        self.configuration.save()

    def on_preferences_clicked(self, widget):
        self.configuration.save()
        cm = PreferencesDialog(self)
        if cm.run() == Gtk.ResponseType.ACCEPT:
            cm.hide()
            cm.save_preferences()
            self.configuration.read()
        cm.destroy()

    def on_maximize_toggle(self, action, value):
            action.set_state(value)
            if value.get_boolean():
                self.maximize()
            else:
                self.unmaximize()

    def on_row_listened(self, widget, row):
        listened = not row.audio['listened']
        row.set_listened(listened)
        self.update_audio_in_configuration(row.audio)

    def on_row_info(self, widget, row):
        sid = ShowInfoDialog(self, row.audio)
        sid.run()
        sid.hide()
        sid.destroy()

    def get_number_of_tracks(self):
        return len(self.trackview.get_children())

    def play_row_by_index(self, index):
        print('====', index, '====')
        if index >= 0 and index < len(self.trackview.get_children()):
            self.play_row(self.trackview.get_row_at_index(index))

    def play_row_by_audio(self, audio):
        found_row = None
        for index, row in enumerate(self.trackview.get_children()):
            if row.audio == audio:
                found_row = row
                break
        if found_row is not None:
            self.play_row(found_row)

    def get_index_for_audio(self, audio):
        for row in self.trackview.get_children():
            if row.audio == audio:
                return row.index
        return -1

    def play_row(self, row):
        if len(self.trackview.get_children()) > 0:
            self.trackview.get_adjustment().set_value(
                row.get_index() * row.get_allocated_height())
            row.grab_focus()
            if self.active_row is not None and self.active_row == row:
                if self.is_playing:
                    self.player.pause()
                    self.control['play-pause'].get_child().set_from_gicon(
                        Gio.ThemedIcon(name='media-playback-start-symbolic'),
                        Gtk.IconSize.BUTTON)
                    self.control['play-pause'].set_tooltip_text(_('Play'))
                    self.is_playing = False
                else:
                    filename = row.audio['filepath']
                    self.player.set_filename(filename)
                    self.player.set_speed(self.configuration.get('speed'))
                    self.player.set_remove_silence(
                        self.configuration.get('remove_silence'))
                    self.player.set_equalizaer(
                        self.configuration.get('equalizer'))

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
                            float(self.active_row.audio['length']))
                    artists = [self.active_row.audio['artist']]
                    album = self.active_row.audio['album']
                    title = self.active_row.audio['title']
                    album_art = 'file://' + get_thumbnail_filename_for_audio(
                        self.active_row.audio)
                    self.sound_menu.song_changed(artists, album,
                                                 title,
                                                 album_art)
                    self.sound_menu.signal_playing()

                    self.notification.update('{0} - {1}'.format(
                        'lplayer',
                        album),
                        title,
                        album_art)
                    self.notification.show()

                    if self.active_row.audio['position'] > 0 and\
                            self.active_row.audio['position'] <= 1:
                        self.player.set_position(
                            self.active_row.audio['position'] *
                            float(self.active_row.audio['length']))
                    self.player.play()
                    self.updater = GLib.timeout_add_seconds(
                        1, self.update_position)
                    self.is_playing = True
            else:
                if self.is_playing is True:
                    self.player.pause()
                    self.control['play-pause'].get_child().set_from_gicon(
                        Gio.ThemedIcon(name='media-playback-start-symbolic'),
                        Gtk.IconSize.BUTTON)
                    self.control['play-pause'].set_tooltip_text(_('Play'))
                    self.is_playing = False

                self.set_active_row(row)
                filename = row.audio['filepath']

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
                        float(self.active_row.audio['length']))
                artists = [self.active_row.audio['artist']]
                album = self.active_row.audio['album']
                title = self.active_row.audio['title']
                album_art = 'file://' + get_thumbnail_filename_for_audio(
                    self.active_row.audio)
                self.sound_menu.song_changed(artists, album, title, album_art)
                self.sound_menu.signal_playing()

                self.notification.update('{0} - {1}'.format(
                    'lplayer',
                    album),
                    title,
                    album_art)
                self.notification.show()

                if self.active_row.audio['position'] > 0 and\
                        self.active_row.audio['position'] <= 1:
                    self.player.set_position(
                        self.active_row.audio['position'] *
                        float(self.active_row.audio['length']))
                self.player.play()
                if self.updater is not None and self.updater > 0:
                    try:
                        GLib.source_remove(self.updater)
                    except Exception as e:
                        print(e)
                self.updater = GLib.timeout_add_seconds(
                    1, self.update_position)
                self.is_playing = True

    def update_audios(self):
        audios = self.configuration.get('audios')
        for row in self.trackview.get_children():
            for index, audio in enumerate(audios):
                if row.audio == audio:
                    audios[index] = audio
                    self.configuration.set('audios', audios)
                    break

    def _sound_menu_quit(self):
        """Quit"""
        if self.updater is not None and self.updater > 0:
            try:
                GLib.source_remove(self.updater)
            except Exception as e:
                print(e)
        self.update_audios()
        self.configuration.set('row', self.row)
        self.configuration.save()
        exit(0)

    def _sound_menu_raise(self):
        """Raise"""
        self.present()

    def _sound_menu_is_playing(self):
        return self.player.status == Status.PLAYING

    def _sound_menu_play(self, *args):
        """Play"""
        # self.is_playing = True  # Need to overwrite
        if self.active_row is None:
            self.set_active_row(self.trackview.get_row_at_index(0))
        self.play_row(self.active_row)

    def _sound_menu_stop(self):
        """Pause"""  # TODO
        if self.active_row is not None and self.active_row.is_playing is True:
            self.play_row(self.active_row)

    def _sound_menu_pause(self, *args):
        """Pause"""
        if self.active_row is not None:
            self.play_row(self.active_row)

    def _sound_menu_next(self, *args):
        """Next"""
        self.play_row(self.trackview.get_row_at_index(
            self.get_next_playable_track()))

    def _sound_menu_previous(self, *args):
        """Previous"""
        self.play_row(self.trackview.get_row_at_index(
            self.get_previous_playable_track()))

    def on_row_selected(self, widget, row):
        if row is not None:
            print('row selected', row.audio['title'])
        self.selected_row = row

    def get_next_playable_track(self):
        if self.active_row is not None:
            next = self.active_row.index + 1
            if next >= len(self.trackview.get_children()):
                next = 0
        else:
            next = 0
        return next

    def get_previous_playable_track(self):
        if self.active_row is not None:
            previous = self.active_row.index - 1
            if previous < 0:
                previous = len(self.trackview.get_children()) - 1
        else:
            previous = len(self.trackview.get_children()) - 1
        return previous

    def update_audio_in_configuration(self, audio):
        audios = self.configuration.get('audios')
        for index, anaudio in enumerate(audios):
            if audio == anaudio:
                audios[index] = audio
                self.configuration.set('audios', audios)
                break

    def update_position(self):
        if self.active_row is not None:
            position = self.player.get_position() / float(
                self.active_row.audio['length'])
            if position >= 0:
                self.active_row.set_position(position)

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
                    if self.is_playing is True:
                        self.is_playing = False
                        self.player.pause()
                    self._sound_menu_next()
                self.update_audio_in_configuration(self.active_row.audio)
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
        pass

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
                self.update_audio_in_configuration(self.active_row.audio)
                self.player.set_position(
                    value * float(self.active_row.audio['length']))

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

        equalizer_grid = Gtk.Grid()

        equalizer_grid.set_margin_top(10)
        equalizer_grid.set_margin_bottom(10)
        equalizer_grid.set_margin_left(5)
        equalizer_grid.set_margin_right(5)

        equalizer_grid.set_column_spacing(10)
        equalizer_grid.set_row_spacing(5)

        popover_grid.attach(equalizer_grid, 0, 5, 10, 1)

        for index in range(0, 10):
            band = 'band{0}'.format(index)
            self.control[band] = Gtk.Scale.new_with_range(
                Gtk.Orientation.VERTICAL, -24.0, 12.0, 0.1)
            self.control[band].set_size_request(10, 200)
            self.control[band].set_value(
                self.configuration.get('equalizer')[band])
            self.control[band].connect('value-changed',
                                       self.on_band_changed, band)
            equalizer_grid.attach(self.control[band], index, 0, 1, 1)
        equalizer_grid.show_all()

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
            name='go-previous'), Gtk.IconSize.BUTTON))
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
            name='go-next'), Gtk.IconSize.BUTTON))
        self.control['next'].connect('clicked',
                                     self._sound_menu_next)
        self.play_controls.pack_start(self.control['next'], False, False, 0)

        help_model = Gio.Menu()

        # help_section0_model = Gio.Menu()
        # help_section0_model.append(_('Download all'), 'app.download_all')
        # help_section0_model.append(_('Preferences'), 'app.set_preferences')
        # help_section0 = Gio.MenuItem.new_section(None, help_section0_model)
        # help_model.append_item(help_section0)

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

        help_section6_model = Gio.Menu()
        help_section6_model.append(_('Quit'), 'app.quit')
        help_section6 = Gio.MenuItem.new_section(None, help_section6_model)
        help_model.append_item(help_section6)

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

        self.control['add'] = Gtk.Button()
        self.control['add'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='list-add-symbolic'), Gtk.IconSize.BUTTON))
        self.control['add'].connect('clicked', self.on_add_track)
        hb.pack_end(self.control['add'])

    def on_band_changed(self, widget, band):
        equalizer = self.configuration.get('equalizer')
        equalizer[band] = widget.get_value()
        self.configuration.set('equalizer', equalizer)
        self.player.set_equalizer_by_band(int(band[4:]), widget.get_value())

    def on_add_track(self, widget):
        dialog = Gtk.FileChooserDialog(_('Please choose music files'),
                                       self,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,
                                        Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name(_('audio files'))
        filter_audio.add_mime_type('audio/mpeg3')
        filter_audio.add_mime_type('audio/mp3')
        filter_audio.add_mime_type('audio/x-mpeg-3')
        filter_audio.add_mime_type('video/mpeg')
        filter_audio.add_mime_type('video/x-mpeg')
        filter_audio.add_mime_type('audio/ogg')
        dialog.add_filter(filter_audio)

        filter_mp3 = Gtk.FileFilter()
        filter_mp3.set_name(_('mp3 files'))
        filter_mp3.add_mime_type('audio/mpeg3')
        filter_mp3.add_mime_type('audio/mp3')
        filter_mp3.add_mime_type('audio/x-mpeg-3')
        filter_mp3.add_mime_type('video/mpeg')
        filter_mp3.add_mime_type('video/x-mpeg')
        dialog.add_filter(filter_mp3)

        filter_ogg = Gtk.FileFilter()
        filter_ogg.set_name(_('ogg files'))
        filter_ogg.add_mime_type('audio/ogg')
        dialog.add_filter(filter_ogg)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            GLib.idle_add(dialog.destroy)
            self.add_tracks_sync(filenames)

    def on_remove_track(self, widget):
        if self.active_row is not None:
            if len(self.trackview.get_selected_rows()) > 1:
                msg = _('Are you sure to delete the tracks?')
            else:
                msg = _('Are you sure to delete the track?')
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
                    audio_id = row.audio['hash']
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
                        self.set_active_row(self.trackview.get_row_at_index(0))
            else:
                dialog.destroy()

    def set_active_row(self, row=None):
        if len(self.trackview.get_children()) > 0:
            self.trackview.unselect_all()
            if self.active_row is not None:
                self.active_row.set_active(False)
            self.active_row = row
            self.active_row.set_active(True)
            self.row = self.active_row.index
            if row is not None:
                self.trackview.select_row(row)

    def add_tracks_sync(self, filenames, play=True):
        self.get_root_window().set_cursor(WAIT_CURSOR)
        play_audio = None
        audios = self.configuration.get('audios')
        for index, filename in enumerate(filenames):
            anaudio = Audio(filename)
            exists = False
            for audio in audios:
                if audio == anaudio:
                    if play_audio is None:
                        play_audio = audio
                    exists = True
                    break
            if exists is False:
                audios.append(anaudio)
                row = ListBoxRowWithData(anaudio, len(audios) - 1)
                row.connect('button_info_clicked',
                            self.on_row_info, row)
                row.connect('button_listened_clicked',
                            self.on_row_listened,
                            row)
                row.show()
                if play_audio is None:
                    play_audio = row.audio
                self.trackview.add(row)
        self.trackview.show_all()
        self.configuration.set('audios', audios)
        self.configuration.save()

        self.get_root_window().set_cursor(DEFAULT_CURSOR)
        if play is True and play_audio is not None:
            self.play_row_by_audio(play_audio)

    def add_tracks(self, filenames, play=True):

        def on_add_track_in_thread_done(result, error):
            self.get_root_window().set_cursor(DEFAULT_CURSOR)
            if error is None and play is True and result is not None:
                self.play_row_by_audio(result)

        @async_function(on_done=on_add_track_in_thread_done)
        def do_add_tracks_in_thread(filenames):
            play_audio = None
            audios = self.configuration.get('audios')
            for index, filename in enumerate(filenames):
                anaudio = Audio(filename)
                exists = False
                for audio in audios:
                    if audio == anaudio:
                        if play_audio is None:
                            play_audio = audio
                        exists = True
                        break
                if exists is False:
                    audios.append(anaudio)
                    row = ListBoxRowWithData(anaudio, len(audios) - 1)
                    row.connect('button_info_clicked',
                                self.on_row_info, row)
                    row.connect('button_listened_clicked',
                                self.on_row_listened,
                                row)
                    row.show()
                    if play_audio is None:
                        play_audio = row.audio
                    self.trackview.add(row)
            self.trackview.show_all()
            self.configuration.set('audios', audios)
            self.configuration.save()
            return play_audio

        self.get_root_window().set_cursor(WAIT_CURSOR)
        do_add_tracks_in_thread(filenames)

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
