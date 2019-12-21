#!/usr/bin/python

import HD44780_I2C
import mpd
import time

# Configuration here

# tick time: delay in seconds between checks of mpd state
tick_time = 0.1
# scrolling delay - specified in ticks
scroll_delay = 4 # == 0.4s

# for 1602 use these:
line_length = 16
num_lines = 2

# background light timeout - specified in ticks
#bg_timeout = 50 # == 5 seconds
bg_timeout = 600 # == 1 minute

# Implementation starts here

CUSTOM_CHARS = (
 ( # 0 - play
 0b01000,
 0b01100,
 0b01110,
 0b01111,
 0b01110,
 0b01100,
 0b01000,
 0b00000),
 ( # 1 - pause
 0b11011,
 0b11011,
 0b11011,
 0b11011,
 0b11011,
 0b11011,
 0b11011,
 0b00000),
 ( # 2 - stop
 0b00000,
 0b11111,
 0b11111,
 0b11111,
 0b11111,
 0b11111,
 0b00000,
 0b00000),
 ( # 3 - repeat
 0b01000,
 0b11110,
 0b01001,
 0b00000,
 0b10010,
 0b01111,
 0b00010,
 0b00000),
 ( # 4 - single
 0b00000,
 0b00100,
 0b01100,
 0b00100,
 0b00100,
 0b00100,
 0b00000,
 0b00000)
)
PLAY = '\x00'
PAUSE = '\x01'
STOP = '\x02'
REPEAT = '\x03'
SINGLE = '\x04'

def _connect():
    mpc = mpd.MPDClient()
    mpc.connect("/var/run/mpd/socket", 0)
    return mpc


def _disconnect(mpc):
    mpc.close()
    mpc.disconnect()

def get_key(d, key):
    try:
        return d[key]
    except KeyError:
        return None

def get_mpd_status(mpc):
    stat = mpc.status()
    song = mpc.currentsong()
    extract = {}
    for key in ('repeat','random','state','elapsed','volume','single','duration'):
        extract[key] = get_key(stat,key)
    for key in ('title','track','artist'):
        extract[key] = get_key(song,key)
    return extract


def state_to_strings(state):
    # 1st line: track id: song title - artist name
    if state['state'] == 'stop':
        line1 = ' ' * line_length
    else:
        line1 = '%s: %s - %s' % (state['track'], state['title'], state['artist'])
    # 2nd line: flags, spacer, play/pause, time elapsed/song duration
    # "SR_X 01:23/04:56"
    try:
        time = int(float(state['elapsed']))
    except TypeError:
        time = 0
    try:
        length = int(float(state['duration']))
    except TypeError:
        length = 0
    state_symbol = STOP
    if state['state'] == 'play':
        state_symbol = PLAY
    elif state['state'] == 'pause':
        state_symbol = PAUSE
    spacer = ' '*(line_length-15)
    rep_symbol = ' '
    if state['single'] == '1':
        rep_symbol = SINGLE
    elif state['repeat'] == '1':
        rep_symbol = REPEAT
    shuffle_symbol = '-'
    if state['random'] == '1':
        shuffle_symbol = '~'
    line2_symbols = shuffle_symbol + rep_symbol + spacer + state_symbol
    line2 = '%s %02d:%02d/%02d:%02d' % (line2_symbols, time/60, time%60, length/60, length%60)
    return ( line1, line2 )


class ScrollLine:
    def __init__(self, lcd, line, length, scroll_delay, string=''):
        self.lcd = lcd
        self.line = line
        self.length = length
        self.scroll_delay = scroll_delay
        self.string = None
        self.set_string(string)

    def set_string(self, string):
        if string == self.string:
            return
        self.string = string
        self.strlength = len(string)
        if self.strlength > self.length:
            self.scrolling = True
            self.scroll_ticks = 0
            self.scroll_pos = 0
            self.scroll_string = string + ' -- ' # delimiter for wrap around
            self.strlength = len(self.scroll_string)
        else:
            self.scrolling = False
            disp_string = string + (' '*(self.length - self.strlength))
            self.lcd.display_string(disp_string, self.line)

    def tick(self):
        if self.scrolling:
            if self.scroll_ticks == 0:
                disp_string = (self.scroll_string*2)[self.scroll_pos:self.scroll_pos+self.length]
                self.lcd.display_string(disp_string, self.line)
                self.scroll_pos = (self.scroll_pos + 1) % self.strlength
            self.scroll_ticks = (self.scroll_ticks + 1) % self.scroll_delay

# Program starts here

lcd = HD44780_I2C.lcd()
lcd.clear()
lcd.load_custom_chars(CUSTOM_CHARS)

mpc = _connect()
old_state = None

lines = []
for i in range(1, num_lines+1):
    lines.append(ScrollLine(lcd, i, line_length, scroll_delay))

time_since_change = 0
while True:
    state = get_mpd_status(mpc)
    if state != old_state:
        new_lcd_strings = state_to_strings(state)
        for i in range(0,num_lines):
            lines[i].set_string(new_lcd_strings[i])
        time_since_change = 0
        lcd.backlight(1)
    else:
        time_since_change = time_since_change + 1

    for l in lines:
        l.tick()

    if time_since_change == bg_timeout:
        lcd.backlight(0)

    old_state = state
    time.sleep(tick_time)

