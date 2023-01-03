"""
Copyright (C) 2022 Mauricio Bustos (m@bustos.org)
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
MARV_M = 0x0001
MARV_A = 0x0002
MARV_R = 0x0004
MARV_V = 0x0008
MARV = 0x000F
HEART = 0x0010
LINDS_L = 0x0020
LINDS_I = 0x0040
LINDS_N = 0x0080
LINDS_D = 0x0100
LINDS_S = 0x0200
LINDS = 0x03F0

DISPLAY_MAPS = {
    "MARV_M": MARV_M,
    "MARV_A": MARV_A,
    "MARV_R": MARV_R,
    "MARV_V": MARV_V,
    "MARV": MARV,
    "HEART": HEART,
    "LINDS_L": LINDS_L,
    "LINDS_I": LINDS_I,
    "LINDS_N": LINDS_N,
    "LINDS_D": LINDS_D,
    "LINDS_S": LINDS_S,
    "LINDS": LINDS,
    "FULL": MARV | HEART | LINDS,
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

LOGGER = logging.getLogger("blm-sign")

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

MESSAGE_LENGTH = 10


def set_timing(name: str, value):
    """ Set parameter values """
    global FAST, MEDIUM, SLOW, TIMES
    LOGGER.info(f"{name}: {value}")
    if name == "fast":
        FAST = value
    if name == "medium:":
        MEDIUM = value
    if name == "slow":
        SLOW = value
    if name == "times":
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
    push_data(DISPLAY_MAPS["FULL"])


def first_then_scroll():
    """ First letter then full """
    display = MARV_M | HEART | LINDS_L
    for i in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(SLOW)
    clear()


def one_at_a_time():
    """ One at a time """
    delay = MEDIUM
    for i in range(0, int(TIMES)):
        push_data(DISPLAY_MAPS["MARV"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["HEART"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["LINDS"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["HEART"])
        time.sleep(delay)
        delay -= 0.1
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
        push_data(0)


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


def sparkle_off():
    """Forwards then back"""
    clear()


ANIMATION_ORDER = {
    1: startup,
    2: window,
    3: first_then_scroll,
    4: scroll,
    5: one_at_a_time,
    6: startup,
    7: scroll,
    8: first_then_scroll,
}
