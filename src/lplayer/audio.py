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


import mutagen
import hashlib
import base64
import os
from .utils import create_thumbnail_for_audio


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
    FORMAT_M4A = 3

    GENRE_UNKNOWN = 0

    def __init__(self, filepath):
        self.set_file(filepath)

    def set_file(self, filepath):
        self['filepath'] = filepath
        audio = mutagen.File(filepath)
        self['hash'] = md5(filepath)
        self['title'] = os.path.splitext(os.path.basename(filepath))[0]
        self['artist'] = ''
        self['album'] = ''
        self['year'] = ''
        self['length'] = 0
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
                    thumbnail_base64 = base64.b64encode(
                        audio.tags['APIC:'].data).decode()
                else:
                    thumbnail_base64 = None
                create_thumbnail_for_audio(self['hash'], thumbnail_base64)
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
            thumbnail_base64 = get_data_from_metadata(audio.tags,
                                                      'metada_block_picture')
            create_thumbnail_for_audio(self['hash'], thumbnail_base64)
            self['length'] = audio.info.length
            self['channels'] = audio.info.channels
            self['sample rate'] = audio.info.sample_rate
            self['bitrate'] = int(audio.info.bitrate / 1000.0)
            self['ext'] = 'ogg'
        elif type(audio.info) == mutagen.flac.StreamInfo:
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
            thumbnail_base64 = get_image_from_flac(audio)
            create_thumbnail_for_audio(self['hash'], thumbnail_base64)
            self['length'] = audio.info.length
            self['channels'] = audio.info.channels
            self['sample rate'] = audio.info.sample_rate
            self['bitrate'] = 0  # int(audio.info.bitrate / 1000.0)
            self['ext'] = 'flac'
        elif type(audio.info) == mutagen.mp4.MP4Info:
            self['type'] = Audio.FORMAT_M4A
            if len(audio.tags['\xa9nam']) > 0:
                self['title'] = audio.tags['\xa9nam'][0]
            else:
                self['title'] = ''
            if len(audio.tags['\xa9ART']) > 0:
                self['artist'] = audio.tags['\xa9ART'][0]
            else:
                self['artist'] = ''
            if len(audio.tags['\xa9alb']) > 0:
                self['album'] = audio.tags['\xa9alb'][0]
            else:
                self['album'] = ''
            if len(audio.tags['\xa9day']) > 0:
                self['year'] = audio.tags['\xa9day'][0]
            else:
                self['year'] = ''
            self['length'] = audio.info.length
            self['channels'] = audio.info.channels
            self['sample rate'] = audio.info.sample_rate
            self['bitrate'] = int(audio.info.bitrate / 1000.0)
            self['ext'] = 'm4a'
            if len(audio.tags['covr']) > 0:
                thumbnail_base64 = base64.b64encode(
                    audio.tags['covr'][0]).decode()
            else:
                thumbnail_base64 = None
            create_thumbnail_for_audio(self['hash'], thumbnail_base64)
        self['genre'] = Audio.GENRE_UNKNOWN
        self['listened'] = False
        self['position'] = 0
        if self['length'] == 0:
            raise Exception

    def __eq__(self, other):
        return self['hash'] == other['hash']

    def __str__(self):
        string = 'Filepath: %s\n' % self['filepath']
        string += 'Hash: %s\n' % self['hash']
        if self['type'] == Audio.FORMAT_MP3:
            string += 'Type: MP3\n'
        elif self['type'] == Audio.FORMAT_OGG:
            string += 'Type: OGG\n'
        elif self['type'] == Audio.FORMAT_FLAC:
            string += 'Type: FLAC\n'
        elif self['type'] == Audio.FORMAT_M4A:
            string += 'Type: M4A\n'
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
    for afile in glob.glob('/home/lorenzo/Descargas/Telegram Desktop/*.m4a'):
        print('====', afile, '====')
        print(Audio(afile))
        print(type(Audio(afile)['thumbnail_base64']))
    print(Audio('/home/lorenzo/Descargas/AMemoryAway.ogg'))
