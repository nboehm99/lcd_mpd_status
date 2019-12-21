# lcd_mpd_status

Python script to display the current status of the Music Player Daemon (MPD) on a 1602 LCD display
connected via I2C to a Raspberry Pi.

Works perfectly for Phoniebox :-)

## Features

* 1st line shows track number, title and artist.
  * Text scrolls, if it doesn't fit in the line (means: nearly always).
* 2nd line shows status information:
  * shuffle on/off
  * repeat on/off
  * repeat single track
  * play/pause/stop
  * elapsed time of current track 
  * duration of current track
* Turn off backlight after inactivity.

## Installation

### Dependencies

t.b.d.

### Configuration

t.b.d.

### Setting up as a service

If you want to run this script automatically from start, you can add it as a
systemd service using the following commands:

    chmod +x lcd_mpd_status.py
    sudo cp lcd_mpd_status.service.template /etc/systemd/system/lcd-mpd-status.service
    # edit /etc/systemd/system/lcd-mpd-status.service and enter the path to the script
    sudo systemctl enable lcd-mpd-status
