# yoaup

yoaup is a simple application to listen youtube audios. This app download the audio for the selected video in YouTube and convert to OGG format to play it.

![](/screenshots/YOAUP_043.png)

You can listen the audios a more speed than the video original, avoid the silences and modify the equalizer. Besides you can listen audios continuosly.

For more information, please visit our website:

https://www.atareao.es/apps/youtube-como-reproductor-de-musica-con-yoaup/

# Requirements

Required dependencies:

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
    youtube-dl

# Install

To install yoaup in Ubuntu, Linux Mint and derivatives, run these commands in a terminal,

    sudo add-apt-repository ppa:atareao/yoaup
    sudo apt update
    sudo apt install yoaup
