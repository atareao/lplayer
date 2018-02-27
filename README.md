# LPLAYER - A simple audio player

**Lplayer** is a simple audio player for simply listening music or whatever you want. The first time, I think in **lplayer** was for listening podcasts, becouse you can set the speed. I normally listen podcast a 1.8x.

![](/screenshots/lplayer_01.png)

You can listen the audios a more speed than the video original, avoid the silences and modify the equalizer. Besides you can listen audios continuosly. lplayer has a complete control over the track you are listening.

![](/screenshots/lplayer_02.png)

Lplayer uses the audio menu to display information about the track you are listening. From the menu, you can go to the next or the previous track, play or pause the track.

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
