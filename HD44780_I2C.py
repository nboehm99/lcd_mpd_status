# -*- coding: utf-8 -*-
"""
HD44780 over I2C driver for Raspberry PI

Originally copied from: https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

Original notes:
    > Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
    > Made available under GNU GENERAL PUBLIC LICENSE
    > 
    > # Modified Python I2C library for Raspberry Pi
    > # as found on http://www.recantha.co.uk/blog/?p=4849
    > # Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
    > # added bits and pieces from various sources
    > # By DenisFromHR (Denis Pleic)

Changes by Niko Boehm <coding@semisane.de>
* Add I2C-address as constructor parameter
* remove "lcd_"-prefix from functions
* add load_custom_char to load a specific custom character
* add some range checks
* refactor display_string[_pos]
"""

import smbus
from time import *

class i2c_device:
    def __init__(self, addr, port=1):
        self.addr = addr
        self.bus = smbus.SMBus(port)

# Write a single command
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

# Write a command and argument
    def write_cmd_arg(self, cmd, data):
        self.bus.write_byte_data(self.addr, cmd, data)
        sleep(0.0001)

# Write a block of data
    def write_block_data(self, cmd, data):
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(0.0001)

# Read a single byte
    def read(self):
        return self.bus.read_byte(self.addr)

# Read
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

# Read a block of data
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)

# LCD I2C Address
DEFAULT_ADDRESS = 0x27

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

# start addresses of the lines
LINE_START_ADDR=(0x80, 0xC0, 0x94, 0xD4)


class lcd:
    #initializes objects and lcd
    def __init__(self, i2c_address=DEFAULT_ADDRESS):
        self.lcd_device = i2c_device(i2c_address)

        self.write(0x03)
        self.write(0x03)
        self.write(0x03)
        self.write(0x02)

        self.write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.write(LCD_CLEARDISPLAY)
        self.write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(0.2)

   # clocks EN to latch command
    def _strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
        sleep(.0001)

    def _write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self._strobe(data)

    # write a command to lcd
    def write(self, cmd, mode=0):
        self._write_four_bits(mode | (cmd & 0xF0))
        self._write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def write_char(self, charvalue, mode=1):
        self._write_four_bits(mode | (charvalue & 0xF0))
        self._write_four_bits(mode | ((charvalue << 4) & 0xF0))
  
    # put string function
    def display_string(self, string, line):
        self.display_string_pos(string, line, 0)

    # clear lcd and set to home
    def clear(self):
        self.write(LCD_CLEARDISPLAY)
        self.write(LCD_RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state): # for state, 1 = on, 0 = off
        if state == 1:
            self.lcd_device.write_cmd(LCD_BACKLIGHT)
        elif state == 0:
            self.lcd_device.write_cmd(LCD_NOBACKLIGHT)

    # add single custom character
    def load_custom_char(self, idx, fontdata):
        if not (0 <= idx < 8):
            return
        if len(fontdata) != 8:
            return
        self.write(0x40 + idx*8);
        for line in fontdata:
            self.write_char(line)         
         
    # add custom characters (0-x)
    def load_custom_chars(self, fontdata):
        for idx in range(0, len(fontdata)):
            self.load_custom_char(idx, fontdata[idx])

    # define precise positioning (addition from the forum)
    def display_string_pos(self, string, line, pos):
        if not (1 <= line <= 4):
            return
        base_addr = LINE_START_ADDR[line-1] + pos
        self.write(base_addr)
        for char in string:
            self.write(ord(char), Rs)


