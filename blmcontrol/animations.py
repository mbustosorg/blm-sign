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
import datetime
import logging
import random
import time

try:
    import smbus
    SMBUS = True
except ImportError:
    SMBUS = False

ENABLE_WORDS = True
if ENABLE_WORDS:
    BLACK_B = 0x0001
    BLACK_L = 0x0002
    BLACK_A = 0x0004
    BLACK_C = 0x0008
    BLACK_K = 0x0010
    BLACK = 0x001F
    LIVES_L = 0x0020
    LIVES_I = 0x0040
    LIVES_V = 0x0080
    LIVES_E = 0x0100
    LIVES_S = 0x0200
    LIVES = 0x03E0
    MATTER_M = 0x0400
    MATTER_A = 0x0800
    MATTER_T1 = 0x1000
    MATTER_T2 = 0x2000
    MATTER_E = 0x4000
    MATTER_R = 0x8000
    MATTER = 0xFC00
else:
    BLACK_B = 0
    BLACK_L = 0
    BLACK_A = 0
    BLACK_C = 0
    BLACK_K = 0
    BLACK = 0
    LIVES_L = 0
    LIVES_I = 0
    LIVES_V = 0
    LIVES_E = 0
    LIVES_S = 0
    LIVES = 0
    MATTER_M = 0
    MATTER_A = 0
    MATTER_T1 = 0
    MATTER_T2 = 0
    MATTER_E = 0
    MATTER_R = 0
    MATTER = 0

HAND_1 = 0x0080
HAND_2 = 0x0001
HAND_3 = 0x0040
HAND_4 = 0x0020
HAND_5 = 0x0008
HAND_6 = 0x0004
SPARE_1 = 0x00400000
SPARE_2 = 0x00800000

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
    'MATTER': MATTER_M | MATTER_A | MATTER_T1 | MATTER_T2 | MATTER_E | MATTER_R,
    'FULL': BLACK | LIVES | MATTER,
    'HAND_1': HAND_1,
    'HAND_2': HAND_2,
    'HAND_3': HAND_3,
    'HAND_4': HAND_4,
    'HAND_5': HAND_5,
    'HAND_6': HAND_6,
    'ALL_HANDS': HAND_1 | HAND_2 | HAND_3 | HAND_4 | HAND_5 | HAND_6,
    'SPARE_1': SPARE_1,
    'SPARE_2': SPARE_2
}

DEVICE1 = 0x26
DEVICE2 = 0x27
IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

if SMBUS:
    BUS = smbus.SMBus(1)
    BUS.write_byte_data(DEVICE1, IODIRA, 0x00)
    BUS.write_byte_data(DEVICE1, IODIRB, 0x00)
    BUS.write_byte_data(DEVICE1, OLATA, 0)
    BUS.write_byte_data(DEVICE1, OLATB, 0)
    BUS.write_byte_data(DEVICE2, IODIRA, 0x00)
    BUS.write_byte_data(DEVICE2, IODIRB, 0x00)
    BUS.write_byte_data(DEVICE2, OLATA, 0)
    BUS.write_byte_data(DEVICE2, OLATB, 0)

LOGGER = logging.getLogger('blm-sign')

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

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


def push_data(value, hands=0xFF):
    """ Push data to I2C devices """
    if SMBUS:
        BUS.write_byte_data(DEVICE1, OLATA, value & 0xFF)
        BUS.write_byte_data(DEVICE1, OLATB, (value & 0xFF00) >> 8)
        BUS.write_byte_data(DEVICE2, OLATA, hands)
        BUS.write_byte_data(DEVICE2, OLATB, 0xFF)


def clear():
    """ Clear the display """
    push_data(DISPLAY_MAPS['FULL'])


def first_then_scroll():
    """ First letter then full """
    display = BLACK_B | LIVES_L | MATTER_M
    for i in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(DISPLAY_MAPS['FULL'])
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
            bit = (0x1 << j) | DISPLAY_MAPS['ALL_HANDS']
            push_data(bit)
            time.sleep(FAST)
    clear()


def random_letters():
    """ Random letter """
    samples = random.sample(range(0, MESSAGE_LENGTH), MESSAGE_LENGTH)
    for i in range(0, int(TIMES)):
        for j in samples:
            bit = (0x1 << j) | DISPLAY_MAPS['ALL_HANDS']
            push_data(bit)
            time.sleep(FAST)
    clear()


def flickering():
    """ Flicker a random couple letters """
    letter = 0x1 << int(random.random() * 16)
    if random.randint(1, 2) == 1:
        primary = 0xFFFF & ~letter
        secondary = 0xFFFF
    else:
        primary = 0xFFFF
        secondary = 0xFFFF & ~letter
    for i in range(0, 45):
        time_sample = random.random()
        push_data(primary)
        time.sleep(time_sample)
        push_data(secondary)
        time.sleep(0.1)
    clear()


def startup():
    """ Simulate starting up a neon light """
    start_time = [random.random() * 1.0 for x in range(0, 16)]
    periods = [(x, x * 2, x * 3, x * 4) for x in start_time]
    start = datetime.datetime.now()
    display = 0
    while display != 0xFFFF:
        delta = datetime.datetime.now() - start
        clock = float(delta.seconds) + delta.microseconds / 1000000.0
        for i, x in enumerate(periods):
            if clock > x[2] + 0.2:
                display = display | 0x1 << i
            elif clock > x[2] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[2]:
                display = display | 0x1 << i
            elif clock > x[1] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[1]:
                display = display | 0x1 << i
            elif clock > x[0] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[0]:
                display = display | 0x1 << i
        push_data(display)
    time.sleep(10)
    clear()


def hand_clasp():
    """ Animate the hand clasp """
    for i in range(0, int(TIMES)):
        push_data(DISPLAY_MAPS['FULL'], HAND_1 | HAND_6)
        time.sleep(SLOW - 0.25)
        push_data(DISPLAY_MAPS['FULL'], HAND_1 | HAND_6 | HAND_2 | HAND_5)
        time.sleep(SLOW - 0.25)
        push_data(DISPLAY_MAPS['FULL'], DISPLAY_MAPS['ALL_HANDS'])
        time.sleep(5)
    clear()


ANIMATION_ORDER = {
    1: hand_clasp,
    2: first_then_scroll,
    3: window,
    4: hand_clasp,
    5: one_at_a_time,
    6: window,
    7: scroll,
    8: first_then_scroll
}
