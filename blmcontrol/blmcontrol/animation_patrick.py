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
import time

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
HEART = 0x0001
CLOVER_1 = 0x0002
CLOVER_2 = 0x0004
CLOVER_3 = 0x0008
CLOVER_4 = 0x0010
CLOVER = 0x001E

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

blmcontrol.animation_utils.MESSAGE_LENGTH = 5


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["HEART"] = HEART
    DISPLAY_MAPS["CLOVER_1"] = CLOVER_1
    DISPLAY_MAPS["CLOVER_2"] = CLOVER_2
    DISPLAY_MAPS["CLOVER_3"] = CLOVER_3
    DISPLAY_MAPS["CLOVER_4"] = CLOVER_4
    DISPLAY_MAPS["CLOVER"] = CLOVER_1 | CLOVER_2 | CLOVER_3 | CLOVER_4
    DISPLAY_MAPS["FULL"] = HEART | CLOVER


def first_then_scroll():
    """ First letter then full """
    display = HEART | CLOVER_1
    for _ in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(SLOW)
    clear()


def one_at_a_time():
    """ One at a time """
    delay = MEDIUM
    for _ in range(0, int(TIMES) * 3):
        push_data(DISPLAY_MAPS["HEART"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["CLOVER"])
        time.sleep(delay)
        if delay > 0.1:
            delay -= 0.1
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
        #if speed_factor > 0.6:
        #    speed_factor -= 0.005
    clear()


def roulette():
    """Roulette wheel on clover"""
    def rotate(value):
        """Rotate value 1 bit to the right"""
        new_value = (value << 1) & 0b00011110
        if not new_value:
            return 0b00000010
        return new_value
    speed_factor = 0.0001
    value = 2
    for _ in range(0, int(TIMES * 8)):
        value = rotate(value)
        push_data(DISPLAY_MAPS["HEART"] | value)
        time.sleep(SLOW * speed_factor)
        speed_factor += 0.0009
    time.sleep(3.0)
    clear()


ANIMATION_ORDER = {
    1: roulette,
    2: window,
    3: roulette,
    4: scroll,
    5: one_at_a_time,
    6: startup,
    7: scroll,
    8: first_then_scroll,
    9: one_at_a_time,
    10: startup,
    11: scroll,
    12: first_then_scroll,
}
