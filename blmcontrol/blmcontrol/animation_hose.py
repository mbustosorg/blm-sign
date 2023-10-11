"""
Copyright (C) 2023 Mauricio Bustos (m@bustos.org)
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
import time
import random

from blmcontrol.animation_utils import (
    TIMES,
    MEDIUM,
    push_data,
    clear,
    window,
    scroll,
    startup,
    DISPLAY_MAPS,
)
import blmcontrol.animation_utils

ENABLE_WORDS = True
STROBE_1 = 0x0001
STROBE_2 = 0x0002
STROBE_3 = 0x0004
STROBE_4 = 0x0008
STROBE_5 = 0x0010
STROBE_6 = 0x0020
STROBE_7 = 0x0040
STROBE_8 = 0x0080
FULL = 0x00FF

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

blmcontrol.animation_utils.MESSAGE_LENGTH = 5


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["STROBE_1"] = STROBE_1
    DISPLAY_MAPS["STROBE_2"] = STROBE_2
    DISPLAY_MAPS["STROBE_3"] = STROBE_3
    DISPLAY_MAPS["STROBE_4"] = STROBE_4
    DISPLAY_MAPS["STROBE_5"] = STROBE_5
    DISPLAY_MAPS["STROBE_6"] = STROBE_6
    DISPLAY_MAPS["STROBE_7"] = STROBE_7
    DISPLAY_MAPS["STROBE_8"] = STROBE_8
    DISPLAY_MAPS["FULL"] = FULL


def sparkle():
    """ Simulate starting up a neon light """
    start_time = [max(random.random() * 1.0, 0.1) for _ in range(0, 16)]
    periods = [(x, x * 2, x * 3, x * 4) for x in start_time]
    start = datetime.datetime.now()
    display = 0
    while display != 0xFFFF:
        delta = datetime.datetime.now() - start
        clock = float(delta.seconds) + delta.microseconds / 1000000.0
        for i, x in enumerate(periods):
            if clock > x[3] + 0.2:
                display = display | 0x1 << i
            elif clock > x[3] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[3]:
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
    time.sleep(3)
    clear()


def heartbeat():
    """ Speeding up heartbeat """
    speed_factor = 1.2
    for _ in range(0, int(TIMES * 10)):
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(FAST * .7 * speed_factor)
        push_data(DISPLAY_MAPS["CLOVER"])
        time.sleep(FAST * 4 * speed_factor)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(FAST * speed_factor)
        push_data(DISPLAY_MAPS["CLOVER"])
        time.sleep(FAST * 4 * speed_factor)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(MEDIUM * .6 * speed_factor)
    clear()


def roulette():
    """Roulette wheel on clover"""
    def rotate(value):
        """Rotate value 1 bit to the right"""
        new_value = (value << 1) & 0b11111110
        if not new_value:
            return 0b00000010
        return new_value
    speed_factor = 0.0001
    value = 2
    for _ in range(0, int(TIMES * 8)):
        value = rotate(value)
        push_data(value)
        time.sleep(SLOW * speed_factor)
        speed_factor += 0.0009
    time.sleep(3.0)
    clear()


ANIMATION_ORDER = {
    1: roulette,
    2: sparkle,
    3: window,
    4: scroll,
    5: sparkle,
    6: startup,
    7: scroll,
    8: sparkle,
    9: startup,
    10: startup,
    11: scroll,
    12: sparkle,
}
