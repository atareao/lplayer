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
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Notify
import os
import json
import mimetypes
import urllib.request
from dbus.mainloop.glib import DBusGMainLoop
from . import comun
from .comun import _
from .sound_menu import SoundMenuControls
from .player import Player
from .player import Status
from .configurator import Configuration
from .listboxrowwithdata import ListBoxRowWithData
from .audio import Audio
from .utils import get_thumbnail_filename_for_audio
from .utils import get_pixbuf_from_base64string
from .utils import get_desktop_environment
from .showinfodialog import ShowInfoDialog
from .preferencesdialog import PreferencesDialog
from .doitinbackground import DoItInBackground
from .progressdialog import ProgressDialog
from .indicator import Indicator

ALLOWED_MIMETYPES = ['application/x-ogg', 'application/ogg',
                     'audio/x-vorbis+ogg', 'audio/x-scpls', 'audio/x-mp3',
                     'audio/x-mpeg', 'audio/mpeg', 'audio/x-mpegurl',
                     'audio/flac', 'audio/m4a', 'audio/x-m4a', 'audio/mp4']

DEFAULT_CURSOR = Gdk.Cursor(Gdk.CursorType.ARROW)
WAIT_CURSOR = Gdk.Cursor(Gdk.CursorType.WATCH)

if get_desktop_environment() == 'cinnamon':
    additional_components = ''
else:
    additional_components = '#progressbar,\n'
CSS = '''
#label:hover,
#label{
    color: rgba(1, 1, 1, 1);
}
#label:selected{
    color: rgba(0, 1, 0, 1);
}
%s
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
}''' % (additional_components)


def get_index_audio(audios, hash):
    for index, audio in enumerate(audios):
        if audio['hash'] == hash:
            return index
    return -1


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_selected_value_in_combo(combo):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 1)


class MainWindow(Gtk.ApplicationWindow):
    __gsignals__ = {
        'text-changed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                         (object,)),
        'save-me': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                    (object,)), }

    def __init__(self, app, files=[]):
        Gtk.ApplicationWindow.__init__(self, application=app)
        self.app = app
        self.set_icon_from_file(comun.ICON)
        self.set_size_request(500, 600)
        self.connect('destroy', self.on_close)

        self.connect('delete_event', self.delete_event)

        self.get_root_window().set_cursor(WAIT_CURSOR)

        self.active_row = None
        self.selected_row = None
        self.is_playing = False
        self.updater = None
        self.configuration = Configuration()
        if self.configuration.get('version') is None or\
                self.configuration.get('version') != comun.VERSION:
            self.configuration.set_defaults()
            self.configuration.set('version', comun.VERSION)
            self.configuration.set('first-time', False)
        self.row = self.configuration.get('row')

        max_action = Gio.SimpleAction.new_stateful(
            "maximize", None, GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.notification = Notify.Notification.new('', '', '')
        self.indicator = Indicator(self)
        self.indicator.connect('play', self._sound_menu_play)
        self.indicator.connect('pause', self._sound_menu_pause)
        self.indicator.connect('previous', self._sound_menu_previous)
        self.indicator.connect('next', self._sound_menu_next)

        self.player = Player()
        self.player.connect('started', self.on_player_started)
        self.player.connect('paused', self.on_player_paused)
        self.player.connect('stopped', self.on_player_stopped)
        self.player.connect('track-end', self.on_track_end)

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
            row.connect('position-changed', self.on_row_position_changed, row)
            row.show()
            row.set_active(False)
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

        self.shorcuts()
        self.load_css()
        
        
        self.connect('realize', self.on_realize)
        self.show_all()
        self.play_controls.set_visible(True)
        self.play_controls.grab_focus()
        self.trackview.unselect_all()
        if self.configuration.get('preset') != 'none':
            select_value_in_combo(self.combobox_presets,
                                  self.configuration.get('preset'))
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
            self.add_tracks_in_background(files)

    def shorcuts(self):
        self.create_shorcut_for_action('play-pause', '<Control>n')
        self.create_shorcut_for_action('next', '<Control>m')
        self.create_shorcut_for_action('previous', '<Control>b')

    def create_shorcut_for_action(self, name, shorcut):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', self.on_action)
        self.add_action(action)
        self.app.add_accelerator(shorcut, 'win.{0}'.format(name), None)

    def on_action(self, widget, option):
        if type(widget) == Gio.SimpleAction:
            option = widget.get_name()
        print(widget, option)
        if option == 'play-pause':
            self._sound_menu_play()
        elif option == 'next':
            self._sound_menu_next()
        elif option == 'previous':
            self._sound_menu_previous()

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
                        if os.path.isdir(filename):
                            print('Is directory')
                            for afile_in_directory in os.listdir(filename):
                                new_file = os.path.join(filename,
                                                        afile_in_directory)
                                if os.path.isfile(new_file):
                                    mime = mimetypes.guess_type(new_file)[0]
                                    if mime in ALLOWED_MIMETYPES:
                                        tracks_to_add.append(new_file)
                        else:
                            mime = mimetypes.guess_type(filename)[0]
                            if mime in ALLOWED_MIMETYPES:
                                tracks_to_add.append(filename)
            if len(tracks_to_add) > 0:
                print(tracks_to_add)
                self.add_tracks_in_background(tracks_to_add)
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
        self.indicator.main_window_is_hidden()
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
        if row is None:
            return
        if row.audio is None or not os.path.exists(row.audio['filepath']):
            self.remove_rows([row])
            return
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
                    self.player.set_equalizer(
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

                    print(type(album), type(title), type(album_art))
                    self.notification.update('{0} - {1}'.format(
                        'lplayer',
                        album),
                        title,
                        album_art)
                    try:
                        self.notification.show()
                    except Exception as e:
                        print(e)

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
                self.player.set_equalizer(self.configuration.get('equalizer'))

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
                try:
                    self.notification.show()
                except Exception as e:
                    print(e)

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
        """Stop"""
        if self.player.status == Status.PLAYING:
            self._sound_menu_pause()
        self.sound_menu.song_changed('', '', '', '')
        self.sound_menu.signal_stoped()

    def _sound_menu_pause(self, *args):
        """Pause"""
        if self.active_row is not None:
            self.play_row(self.active_row)

    def _sound_menu_next(self, *args):
        """Next"""
        if self.active_row is not None:
            next = self.active_row.index + 1
            if next >= len(self.trackview.get_children()):
                next = 0
        else:
            next = 0
        self.play_row(self.trackview.get_row_at_index(next))

    def _sound_menu_previous(self, *args):
        """Previous"""
        if self.active_row is not None:
            previous = self.active_row.index - 1
            if previous < 0:
                previous = len(self.trackview.get_children()) - 1
        else:
            previous = len(self.trackview.get_children()) - 1
        self.play_row(self.trackview.get_row_at_index(previous))

    def on_row_selected(self, widget, row):
        if row is not None:
            print('row selected', row.audio['title'])
            self.indicator.set_current(row.audio['title'], row.audio['hash'])
        self.selected_row = row

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
                if position >= 0.999:
                    pass
                    '''
                    self.active_row.set_listened(True)
                    self.active_row.set_position(0)
                    if self.is_playing is True:
                        self.player.pause()
                        self.control['play-pause'].get_child().set_from_gicon(
                            Gio.ThemedIcon(
                                name='media-playback-start-symbolic'),
                            Gtk.IconSize.BUTTON)
                        self.control['play-pause'].set_tooltip_text(_('Play'))
                        self.is_playing = False
                    if self.configuration.get('play_continuously') is True:
                        self._sound_menu_next()
                    '''
                self.update_audio_in_configuration(self.active_row.audio)
            if self.player.status != Status.PLAYING:
                self.updater = 0
            return self.player.status == Status.PLAYING
        self.updater = 0
        return False

    def on_track_end(self, widget):
        self.active_row.set_listened(True)
        self.active_row.set_position(0)
        if self.is_playing is True:
            self.player.pause()
            self.control['play-pause'].get_child().set_from_gicon(
                Gio.ThemedIcon(
                    name='media-playback-start-symbolic'),
                Gtk.IconSize.BUTTON)
            self.control['play-pause'].set_tooltip_text(_('Play'))
            self.is_playing = False
        if self.configuration.get('play_continuously') is True:
            self._sound_menu_next()
        self.update_audio_in_configuration(self.active_row.audio)

    def on_player_started(self, player, position):
        self.indicator.play()

    def on_player_paused(self, player, position):
        self.indicator.pause()

    def on_player_stopped(self, player, position):
        self.indicator.pause()

    def on_row_selected_changed(self, widget):
        print(widget)
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
        self.control['speed'].set_tooltip_text(_('Speed'))
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
        self.control['remove-silence'].set_tooltip_text(_('Remove silence'))
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
        self.control['play_continuously'].set_tooltip_text(
            _('Play continuously'))
        self.control['play_continuously'].set_active(
            self.configuration.get('play_continuously'))
        self.control['play_continuously'].connect(
            'notify::active', self.on_play_continuously_changed)
        tbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        tbox.add(self.control['play_continuously'])
        popover_grid.attach(tbox, 5, 3, 5, 1)

        popover_grid.attach(Gtk.Label(_('Equalizer')), 0, 4, 10, 1)

        equalizer_grid = Gtk.HBox.new(True, 5)

        equalizer_grid.set_margin_top(10)
        equalizer_grid.set_margin_bottom(10)

        popover_grid.attach(equalizer_grid, 0, 5, 10, 1)

        for index in range(0, 10):
            band = 'band{0}'.format(index)
            self.control[band] = Gtk.Scale.new(
                Gtk.Orientation.VERTICAL,
                Gtk.Adjustment(0, -24, 13, 1, 1, 1))
            self.control[band].set_digits(0)
            self.control[band].set_inverted(True)
            # self.control[band].add_mark(4, Gtk.PositionType.LEFT, None)
            self.control[band].set_has_origin(True)
            self.control[band].set_value_pos(Gtk.PositionType.BOTTOM)
            self.control[band].set_size_request(5, 200)
            self.control[band].set_tooltip_text(_('Help'))
            self.control[band].set_value(
                self.configuration.get('equalizer')[band])
            self.control[band].connect('value-changed',
                                       self.on_band_changed, band)
            equalizer_grid.pack_start(self.control[band], True, True, 0)

        self.control['band0'].set_tooltip_text(_('29 Hz'))
        self.control['band1'].set_tooltip_text(_('59 Hz'))
        self.control['band2'].set_tooltip_text(_('119 Hz'))
        self.control['band3'].set_tooltip_text(_('237 Hz'))
        self.control['band4'].set_tooltip_text(_('474 Hz'))
        self.control['band5'].set_tooltip_text(_('947 Hz'))
        self.control['band6'].set_tooltip_text(_('1889 Hz'))
        self.control['band7'].set_tooltip_text(_('3770 Hz'))
        self.control['band8'].set_tooltip_text(_('7523 Hz'))
        self.control['band9'].set_tooltip_text(_('15011 Hz'))
        equalizer_grid.show_all()

        presets = Gtk.ListStore(str, str)
        presets.append([_('None'), 'none'])
        presets.append([_('Classical'), 'classical'])
        presets.append([_('Club'), 'club'])
        presets.append([_('Dance'), 'dance'])
        presets.append([_('Flat'), 'flat'])
        presets.append([_('Live'), 'live'])
        presets.append([_('Headphone'), 'headphone'])
        presets.append([_('Rock'), 'rock'])
        presets.append([_('Pop'), 'pop'])
        presets.append([_('Full Bass and Treble'), 'full-bass-and-treble'])
        presets.append([_('Full Bass'), 'full-bass'])
        presets.append([_('Full Treble'), 'full-treble'])
        presets.append([_('Soft'), 'soft'])
        presets.append([_('Party'), 'party'])
        presets.append([_('Ska'), 'ska'])
        presets.append([_('Soft Rock'), 'soft-rock'])
        presets.append([_('Large Hall'), 'large-hall'])
        presets.append([_('Reggae'), 'reggae'])
        presets.append([_('Techno'), 'techno'])

        self.combobox_presets = Gtk.ComboBox.new()
        self.combobox_presets.set_tooltip_text(_('Equalizer presets'))
        self.combobox_presets.set_model(presets)
        cell1 = Gtk.CellRendererText()
        self.combobox_presets.pack_start(cell1, True)
        self.combobox_presets.add_attribute(cell1, 'text', 0)
        self.combobox_presets.set_active(0)
        self.combobox_presets.connect('changed', self.on_preset_changed)
        popover_grid.attach(self.combobox_presets, 0, 6, 10, 1)

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
        self.control['help'].set_tooltip_text(_('Help'))
        self.control['help'].set_menu_model(help_model)
        self.control['help'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='open-menu-symbolic'), Gtk.IconSize.BUTTON))
        hb.pack_end(self.control['help'])

        self.control['remove'] = Gtk.Button()
        self.control['remove'].set_tooltip_text(_('Remove tracks'))
        self.control['remove'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='list-remove-symbolic'), Gtk.IconSize.BUTTON))
        self.control['remove'].connect('clicked', self.on_remove_track)
        hb.pack_end(self.control['remove'])

        self.control['add'] = Gtk.Button()
        self.control['add'].set_tooltip_text(_('Add tracks'))
        self.control['add'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='list-add-symbolic'), Gtk.IconSize.BUTTON))
        self.control['add'].connect('clicked', self.on_add_track)
        hb.pack_end(self.control['add'])

    def on_preset_changed(self, widget):
        print('changed')
        preset = get_selected_value_in_combo(widget)
        self.configuration.set('preset', preset)
        values = []
        # presets https://gist.github.com/kra3/9781800
        if preset == 'none':
            values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif preset == 'classical':
            values = [0.375, 0.375, 0.375, 0.375, 0.375, 0.375, -4.5, -4.5,
                      -4.5, -6.0]
        elif preset == 'club':
            values = [0.375, 0.375, 2.25, 3.75, 3.75, 3.75, 2.25, 0.375,
                      0.375, 0.375]
        elif preset == 'dance':
            values = [6, 4.5, 1.5, 0, 0, -3.75, -4.5, -4.5,
                      0, 0]
        elif preset == 'flat':
            values = [0.375, 0.375, 0.375, 0.375, 0.375, 0.375, 0.375, 0.375,
                      0.375, 0.375]
        elif preset == 'live':
            values = [-3, 0.375, 2.625, 3.375, 3.75, 3.75, 2.625, 1.875, 1.875,
                      1.5]
        elif preset == 'headphone':
            values = [3, 6.75, 3.375, -2.25, -1.5, 1.125, 3, 6, 7.875, 9]
        elif preset == 'rock':
            values = [4.875, 3, -3.375, -4.875, -2.25, 2.625, 5.625, 6.75,
                      6.75, 6.75]
        elif preset == 'pop':
            values = [-1.125, 3, 4.5, 4.875, 3.375, -0.75, -1.5, -1.5, -1.125,
                      -1.125]
        elif preset == 'full-bass-and-treble':
            values = [4.5, 3.75, 0.375, -4.5, -3, 1.125, 5.25, 6.75, 7.5, 7.5]
        elif preset == 'full-bass':
            values = [6, 6, 6, 3.75, 1.125, -2.625, -5.25, -6.375, -6.75,
                      -6.75]
        elif preset == 'full-treble':
            values = [-6, -6, -6, -2.625, 1.875, 6.75, 9.75, 9.75, 9.75, 10.5]
        elif preset == 'soft':
            values = [3, 1.125, -0.75, -1.5, -0.75, 2.625, 5.25, 6, 6.75, 7.5]
        elif preset == 'party':
            values = [4.5, 4.5, 0.375, 0.375, 0.375, 0.375, 0.375, 0.375, 4.5,
                      4.5]
        elif preset == 'ska':
            values = [-1.5, -3, -2.625, -0.375, 2.625, 3.75, 5.625, 6, 6.75, 6]
        elif preset == 'soft-rock':
            values = [2.625, 2.625, 1.5, -0.375, -2.625, -3.375, -2.25, -0.375,
                      1.875, 5.625]
        elif preset == 'large-hall':
            values = [6.375, 6.375, 3.75, 3.75, 0.375, -3, -3, -3, 0.375,
                      0.375]
        elif preset == 'reggae':
            values = [0.375, 0.375, -0.375, -3.75, 0.375, 4.125, 4.125, 0.375,
                      0.375, 0.375]
        elif preset == 'techno':
            values = [4.875, 3.75, 0.375, -3.375, -3, 0.375, 4.875, 6, 6,
                      5.625]
        if len(values) > 0:
            for index in range(0, 10):
                band = 'band{0}'.format(index)
                self.control[band].set_value(values[index])

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
        filter_audio.add_mime_type('audio/flac')
        filter_audio.add_mime_type('audio/m4a')
        filter_audio.add_mime_type('audio/mp4')
        filter_audio.add_mime_type('audio/x-m4a')
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

        filter_flac = Gtk.FileFilter()
        filter_flac.set_name(_('flac files'))
        filter_flac.add_mime_type('audio/flac')
        dialog.add_filter(filter_flac)

        filter_m4a = Gtk.FileFilter()
        filter_m4a.set_name(_('mp4 files'))
        filter_m4a.add_mime_type('audio/m4a')
        filter_m4a.add_mime_type('audio/mp4')
        filter_m4a.add_mime_type('audio/x-m4a')
        dialog.add_filter(filter_m4a)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            GLib.idle_add(dialog.destroy)
            # self.add_tracks_sync(filenames)
            self.add_tracks_in_background(filenames)
        else:
            dialog.destroy()

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
                self.remove_rows(self.trackview.get_selected_rows())
            else:
                dialog.destroy()

    def remove_rows(self, rows):
        audios = self.configuration.get('audios')
        for row in rows:
            audios.remove(row.audio)
            self.trackview.remove(row)
            audio_id = row.audio['hash']
            file_thumbnail = os.path.join(
                comun.THUMBNAILS_DIR,
                '{0}.{1}'.format(audio_id, 'png'))
            if os.path.exists(file_thumbnail):
                os.remove(file_thumbnail)
        self.configuration.set('audios', audios)
        self.trackview.show_all()
        if self.active_row.audio == row.audio and\
                len(self.trackview.get_children()) > 0:
            self.set_active_row(self.trackview.get_row_at_index(0))

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

    def add_track(self, filename):
        audios = self.configuration.get('audios')
        try:
            anaudio = Audio(filename)
        except Exception as e:
            print(e)
            return
        exists = False
        for audio in audios:
            if audio == anaudio:
                exists = True
                break
        if exists is False:
            audios.append(anaudio)
            row = ListBoxRowWithData(anaudio, len(audios) - 1)
            row.set_active(False)
            row.connect('button_info_clicked',
                        self.on_row_info, row)
            row.connect('button_listened_clicked',
                        self.on_row_listened,
                        row)
            row.connect('position-changed',
                        self.on_row_position_changed,
                        row)
            GLib.idle_add(row.show)
            GLib.idle_add(self.trackview.add, row)
        GLib.idle_add(self.trackview.show_all)
        self.configuration.set('audios', audios)
        self.configuration.save()

    def on_row_position_changed(self, widget, position, row):
        print(widget, position, row)
        if self.active_row is not None:
            self.control['position'].handler_block_by_func(
                self.on_position_button_changed)

            self.control['label-position'].set_label(
                _('Position' + ': {0}%'.format(int(position))))
            value = float(position) / 100.0
            if value >= 0.0 and value <= 1.0:
                self.active_row.set_position(value)
                self.update_audio_in_configuration(self.active_row.audio)
                self.player.set_position(
                    value * float(self.active_row.audio['length']))
            self.control['position'].handler_unblock_by_func(
                self.on_position_button_changed)

    def add_tracks_in_background(self, filenames, play=True):
        if len(filenames) > 0:
            number_of_audios = len(self.configuration.get('audios'))
            diib = DoItInBackground(self.add_track, filenames)
            progreso = ProgressDialog(_('Adding new tracks'), self)
            progreso.set_number_of_elements(len(filenames))
            diib.connect('started_one', progreso.set_element)
            # diib.connect('done_one', progreso.increase)
            diib.connect('ended', progreso.close)
            progreso.connect('i-want-stop', diib.stop)
            diib.start()
            progreso.run()
            if play is True:
                if len(self.configuration.get('audios')) > number_of_audios:
                    self.play_row_by_index(number_of_audios)
                else:
                    try:
                        audio = Audio(filenames[0])
                        self.play_row_by_audio(audio)
                    except Exception as e:
                        print(e)

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
                row.connect('position-changed',
                            self.on_row_position_changed,
                            row)
                row.show()
                row.set_active(False)
                if play_audio is None:
                    play_audio = row.audio
                self.trackview.add(row)
        self.trackview.show_all()
        self.configuration.set('audios', audios)
        self.configuration.save()

        self.get_root_window().set_cursor(DEFAULT_CURSOR)
        if play is True and play_audio is not None:
            self.play_row_by_audio(play_audio)

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

    def on_realize(self, *_):
        monitor = Gdk.Display.get_primary_monitor(Gdk.Display.get_default())
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = self.get_preferred_width()[0]
        height = self.get_preferred_height()[0]
        print(width, height)
        self.move((monitor_width - width)/2, (monitor_height - height)/2)