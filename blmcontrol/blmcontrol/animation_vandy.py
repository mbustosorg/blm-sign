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
V = 0x0002

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

blmcontrol.animation_utils.MESSAGE_LENGTH = 5


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["HEART"] = HEART
    DISPLAY_MAPS["V"] = V
    DISPLAY_MAPS["FULL"] = HEART | V


def one_at_a_time():
    """ One at a time """
    delay = MEDIUM
    for _ in range(0, int(TIMES) * 3):
        push_data(DISPLAY_MAPS["HEART"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["V"])
        time.sleep(delay)
        if delay > 0.1:
            delay -= 0.1
    clear()


def heartbeat():
    """ Speeding up heartbeat """
    increment = 0.0025
    speed_factor = 1.3
    transitioning = -1
    direction = True
    for _ in range(0, int(TIMES * 45)):
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(FAST * .7 * speed_factor)
        push_data(DISPLAY_MAPS["V"])
        time.sleep(FAST * 2.5 * speed_factor)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(FAST * speed_factor)
        push_data(DISPLAY_MAPS["V"])
        time.sleep(FAST * 2.5 * speed_factor)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(MEDIUM * .4 * speed_factor)
        if transitioning > -1:
            transitioning += 1
            if transitioning > 50:
                transitioning = -1
        if direction:
            if speed_factor > 0.75:
                speed_factor -= increment
            else:
                direction = not direction
                transitioning = 0
        else:
            if speed_factor < 1.3:
                speed_factor += increment
            else:
                direction = not direction
    clear()


ANIMATION_ORDER = {
    1: one_at_a_time,
    2: heartbeat,
}
