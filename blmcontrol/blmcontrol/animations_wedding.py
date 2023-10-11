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
import time

from blmcontrol.animation_utils import (
    TIMES,
    SLOW,
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

blmcontrol.animation_utils.MESSAGE_LENGTH = 10


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["MARV_M"] = (MARV_M,)
    DISPLAY_MAPS["MARV_A"] = (MARV_A,)
    DISPLAY_MAPS["MARV_R"] = (MARV_R,)
    DISPLAY_MAPS["MARV_V"] = (MARV_V,)
    DISPLAY_MAPS["MARV"] = (MARV,)
    DISPLAY_MAPS["HEART"] = (HEART,)
    DISPLAY_MAPS["LINDS_L"] = (LINDS_L,)
    DISPLAY_MAPS["LINDS_I"] = (LINDS_I,)
    DISPLAY_MAPS["LINDS_N"] = (LINDS_N,)
    DISPLAY_MAPS["LINDS_D"] = (LINDS_D,)
    DISPLAY_MAPS["LINDS_S"] = (LINDS_S,)
    DISPLAY_MAPS["LINDS"] = (LINDS,)
    DISPLAY_MAPS["FULL"] = (MARV | HEART | LINDS,)


def one_at_a_time():
    """ One at a time """
    delay = MEDIUM
    for _ in range(0, int(TIMES)):
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


def first_then_scroll():
    """ First letter then full """
    display = MARV_M | HEART | LINDS
    for _ in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(SLOW)
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
