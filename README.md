# LPLAYER - A simple audio player

**Lplayer** is a simple audio player for simply listening music or whatever you want. The first time I thinked about **lplayer** was for listening podcasts. **lplayer** can set the speed. I normally listen podcasts a 1.8x. So this option was very important for me. But not only. This audio player must have to avoid silences to play podcasts.

**lplayer** can play several audio formats,

* MP3
* OGG
* FLAC
* M4a

After I added the option to play several audio format, I thinked that this audio player must include an equalizer, so you can configure the player as you want. Besides, **lplayer** incorporates some equalizer presets, so it's more easy to configure it.

![](/screenshots/lplayer_01.png)

**lplayer** is thinked as a very simple audio player that it doesn't disturb your concentration. Only to play audio and if it is possible in background.

![](/screenshots/lplayer_02.png)

In order to not disturb, **lplayer** is integrated in the sound menu in Linux Mint Cinnamon and Ubuntu. With latest versions of Ubuntu you will need a extension for it. Lplayer uses the audio menu to display information about the track you are listening. From the menu, you can go to the next or the previous track, play, pause and stop the track.

![](/screenshots/lplayer_03.png)


For more information, please visit our website:

[https://www.atareao.es/aplicacion/lplayer/](lplayer)

* [Code](https://github.com/atareao/lplayer)
* [Bugs](https://bugs.launchpad.net/lplayer)
* [Blueprints](https://blueprints.launchpad.net/lplayer)
* [Translations](https://translations.launchpad.net/lplayer)
* [Answers](https://answers.launchpad.net/lplayer)
* [Page project in Launchpad](https://launchpad.net/lplayer)

![](/screenshots/lplayer_04.png)

# Requirements

Required dependencies:

```
    python3,
    python3-gi,
    python3-dbus,
    python3-requests,
    python3-dbus,
    python3-pil,
    gir1.2-gtk-3.0,
    gir1.2-gdkpixbuf-2.0,
    gir1.2-notify-0.7,
    gir1.2-gstreamer-1.0,
    gir1.2-gst-plugins-base-1.0,
    gstreamer1.0-tools,
    gstreamer1.0-plugins-good,
    gstreamer1.0-plugins-ugly,
    gstreamer1.0-plugins-bad,
    gstreamer1.0-libav,
```

# Install

To install lplayer in Ubuntu, Linux Mint and derivatives, run these commands in a terminal,

```
    sudo add-apt-repository ppa:atareao/lplayer
    sudo apt update
    sudo apt install lplayer
```
