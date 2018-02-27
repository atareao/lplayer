#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# audio.py
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


import mutagen
import hashlib
import base64
import os


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_data_from_metadata(tags, info):
    for tag in tags:
        if tag[0].lower() == info.lower():
            return tag[1]
    return ''


def get_image_from_flac(audio):
    for picture in audio.pictures:
        if picture.type == mutagen.id3.PictureType.COVER_FRONT:
            return base64.b64encode(picture.data).decode()
    return None


class Audio(dict):
    FORMAT_MP3 = 0
    FORMAT_OGG = 1
    FORMAT_FLAC = 2

    GENRE_UNKNOWN = 0

    def __init__(self, filepath):
        self.set_file(filepath)

    def set_file(self, filepath):
        self['filepath'] = filepath
        audio = mutagen.File(filepath)
        self['hash'] = md5(filepath)
        if type(audio.info) == mutagen.mp3.MPEGInfo:
            self['type'] = Audio.FORMAT_MP3
            if audio.tags is not None:
                self['title'] =\
                    audio.tags['TIT2'].text[0] if 'TIT2' in audio.tags.keys()\
                    else os.path.splitext(os.path.basename(filepath))[0]
                self['artist'] = audio.tags['TPE1'].text[0] if 'TPE1' in\
                    audio.tags.keys() else ''
                self['album'] = audio.tags['TALB'].text[0] if 'TALB' in\
                    audio.tags.keys() else ''
                if 'TDRC' in audio.tags.keys():
                    self['year'] = str(audio.tags['TDRC'].text[0])
                else:
                    self['year'] = ''
                if 'APIC:' in audio.tags.keys():
                    self['thumbnail_base64'] = base64.b64encode(
                        audio.tags['APIC:'].data).decode()
                else:
                    self['thumbnail_base64'] = None
            else:
                self['title'] = os.path.splitext(os.path.basename(filepath))[0]
                self['artist'] = ''
                self['album'] = ''
                self['year'] = ''
                self['thumbnail_base64'] = None
            if audio.info is not None:
                self['length'] = audio.info.length
                self['channels'] = audio.info.channels
                self['sample rate'] = audio.info.sample_rate
                self['bitrate'] = int(audio.info.bitrate / 1000.0)
            self['ext'] = 'mp3'
        elif type(audio.info) == mutagen.oggvorbis.OggVorbisInfo:
            self['type'] = Audio.FORMAT_OGG
            self['title'] = get_data_from_metadata(audio.tags, 'title')
            if len(self['title']) < 1:
                self['title'] = os.path.splitext(os.path.basename(filepath))[0]
            self['artist'] = get_data_from_metadata(audio.tags, 'artist')
            self['album'] = get_data_from_metadata(audio.tags, 'album')
            self['year'] = get_data_from_metadata(audio.tags, 'year')
            self['thumbnail_base64'] = get_data_from_metadata(
                audio.tags, 'metada_block_picture')
            self['length'] = audio.info.length
            self['channels'] = audio.info.channels
            self['sample rate'] = audio.info.sample_rate
            self['bitrate'] = int(audio.info.bitrate / 1000.0)
            self['ext'] = 'ogg'
        elif type(audio.info) == mutagen.flac.StreamInfo:
            print(audio.tags)
            print(audio.pictures)
            for picture in audio.pictures:
                print(picture.type)
                print(picture.mime)
                print(picture.desc)
            self['type'] = Audio.FORMAT_FLAC
            self['title'] = get_data_from_metadata(audio.tags, 'title')
            if len(self['title']) < 1:
                self['title'] = os.path.splitext(os.path.basename(filepath))[0]
            self['artist'] = get_data_from_metadata(audio.tags, 'artist')
            self['album'] = get_data_from_metadata(audio.tags, 'album')
            if len(self['album']) == 0:
                self['album'] = get_data_from_metadata(audio.tags,
                                                       'albumtitle')
            self['year'] = get_data_from_metadata(audio.tags, 'year')
            print(audio.info)
            self['thumbnail_base64'] = get_image_from_flac(audio)
            self['length'] = audio.info.length
            self['channels'] = audio.info.channels
            self['sample rate'] = audio.info.sample_rate
            self['bitrate'] = 0  # int(audio.info.bitrate / 1000.0)
            self['ext'] = 'flac'

        self['genre'] = Audio.GENRE_UNKNOWN
        self['listened'] = False
        self['position'] = 0

    def __eq__(self, other):
        return self['hash'] == other['hash']

    def __str__(self):
        string = 'Filepath: %s\n' % self['filepath']
        string += 'Hash: %s\n' % self['hash']
        if self['type'] == Audio.FORMAT_MP3:
            string += 'Type: MP3\n'
        elif self['type'] == Audio.FORMAT_OGG:
            string += 'Type: OGG\n'
        string += 'Title: %s\n' % self['title']
        string += 'Artist: %s\n' % self['artist']
        string += 'Album: %s\n' % self['album']
        string += 'Year: %s\n' % self['year']
        string += 'Length: %s s\n' % self['length']
        string += 'Channels: %s\n' % self['channels']
        string += 'Sample Rate: %s\n' % self['sample rate']
        string += 'Bitrate: %s\n' % self['bitrate']
        string += 'Extension: %s\n' % self['ext']
        if self['genre'] == Audio.GENRE_UNKNOWN:
            string += 'Genre: Unknown\n'
        if self['listened'] is True:
            string += 'Listened: True\n'
        else:
            string += 'Listened: False\n'
        string += 'Position: %s\n' % self['position']
        return string


if __name__ == '__main__':
    import glob
    for afile in glob.glob('/home/lorenzo/Descargas/Telegram Desktop/*.flac'):
        print('====', afile, '====')
        print(Audio(afile))
        print(type(Audio(afile)['thumbnail_base64']))
    print(Audio('/home/lorenzo/Descargas/AMemoryAway.ogg'))
