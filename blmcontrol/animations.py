"""
    Copyright (C) 2020 Mauricio Bustos (m@bustos.org)
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import random
import time

import smbus

BLACK_B = 0x0001
BLACK_L = 0x0002
BLACK_A = 0x0004
BLACK_C = 0x0008
BLACK_K = 0x0010
LIVES_L = 0x0020
LIVES_I = 0x0040
LIVES_V = 0x0080
LIVES_E = 0x0100
LIVES_S = 0x0200
MATTER_M = 0x0400
MATTER_A = 0x0800
MATTER_T1 = 0x1000
MATTER_T2 = 0x2000
MATTER_E = 0x4000
MATTER_R = 0x8000

DISPLAY_MAPS = {
    'BLACK_B': BLACK_B,
    'BLACK_L': BLACK_L,
    'BLACK_A': BLACK_A,
    'BLACK_C': BLACK_C,
    'BLACK_K': BLACK_K,
    'BLACK': BLACK_B | BLACK_L | BLACK_A | BLACK_C | BLACK_K,
    'LIVES_L': LIVES_L,
    'LIVES_I': LIVES_I,
    'LIVES_V': LIVES_V,
    'LIVES_E': LIVES_E,
    'LIVES_S': LIVES_S,
    'LIVES': LIVES_L | LIVES_I | LIVES_V | LIVES_E | LIVES_S,
    'MATTER_M': MATTER_M,
    'MATTER_A': MATTER_A,
    'MATTER_T1': MATTER_T1,
    'MATTER_T2': MATTER_T2,
    'MATTER_E': MATTER_E,
    'MATTER_R': MATTER_R,
    'MATTER': MATTER_M | MATTER_A | MATTER_T1 | MATTER_T2 | MATTER_E | MATTER_R
}
FULL = DISPLAY_MAPS['BLACK'] | DISPLAY_MAPS['LIVES'] | DISPLAY_MAPS['MATTER']

DEVICE1 = 0x26
DEVICE2 = 0x27
IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

BUS = smbus.SMBus(1)

BUS.write_byte_data(DEVICE1, IODIRA, 0x00)
BUS.write_byte_data(DEVICE1, IODIRB, 0x00)
BUS.write_byte_data(DEVICE1, OLATA, 0)
BUS.write_byte_data(DEVICE1, OLATB, 0)

LOGGER = logging.getLogger('blm-sign')

FAST = 0.1
MEDIUM = 1.0
SLOW = 3.0
TIMES = 3

MESSAGE_LENGTH = 16


def set_timing(name: str, value):
    """ Set parameter values """
    global FAST, MEDIUM, SLOW, TIMES
    LOGGER.info(f'{name}: {value}')
    if name == 'fast':
        FAST = value
    if name == 'medium:':
        MEDIUM = value
    if name == 'slow':
        SLOW = value
    if name == 'times':
        TIMES = int(value)


def push_data(value):
    """ Push data to I2C devices """
    BUS.write_byte_data(DEVICE1, OLATA, value & 0xFF)
    BUS.write_byte_data(DEVICE1, OLATB, (value & 0xFF00) >> 8)


def clear():
    """ Clear the display """
    push_data(0)


def first_then_scroll():
    """ First letter then full """
    display = BLACK_B | LIVES_L | MATTER_M
    for i in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(FULL)
        time.sleep(SLOW)
    clear()


def one_at_a_time():
    """ One at at time """
    for i in range(0, int(TIMES)):
        push_data(DISPLAY_MAPS['BLACK'])
        time.sleep(MEDIUM)
        push_data(DISPLAY_MAPS['LIVES'])
        time.sleep(MEDIUM)
        push_data(DISPLAY_MAPS['MATTER'])
        time.sleep(MEDIUM)
    clear()


def window():
    """ Slide window across """
    for i in range(0, int(TIMES)):
        bit = 0
        for j in range(0, MESSAGE_LENGTH):
            bit = bit | 0x1 << j
            push_data(bit)
            time.sleep(FAST)
        for j in range(0, MESSAGE_LENGTH):
            bit = 0xFFFF << (j + 1)
            push_data(bit)
            time.sleep(FAST)
    clear()


def scroll():
    """ Left to right one letter at time """
    for i in range(0, int(TIMES)):
        for j in range(0, MESSAGE_LENGTH):
            bit = 0x1 << j
            push_data(bit)
            time.sleep(FAST)
    clear()


def random_letters():
    """ Random letter """
    samples = random.sample(range(0, MESSAGE_LENGTH), MESSAGE_LENGTH)
    for i in range(0, int(TIMES)):
        for j in samples:
            bit = 0x1 << j
            push_data(bit)
            time.sleep(FAST)
    clear()

