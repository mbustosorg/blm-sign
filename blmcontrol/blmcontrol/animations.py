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
from functools import partial
import random
import time

from blmcontrol.animation_utils import (
    TIMES,
    MEDIUM,
    push_data,
    clear,
    startup_shutdown,
    scroll,
    DISPLAY_MAPS,
    startup,
)

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
    BLACK_B = 0x0001
    BLACK_L = 0
    BLACK_A = 0
    BLACK_C = 0
    BLACK_K = 0
    BLACK = 0x0001
    LIVES_L = 0x0020
    LIVES_I = 0
    LIVES_V = 0
    LIVES_E = 0
    LIVES_S = 0
    LIVES = 0x0020
    MATTER_M = 0x0400
    MATTER_A = 0
    MATTER_T1 = 0
    MATTER_T2 = 0
    MATTER_E = 0
    MATTER_R = 0
    MATTER = 0x0400

HAND_1 = 0x0080
HAND_2 = 0x0001
HAND_3 = 0x0040
HAND_4 = 0x0020
HAND_5 = 0x0008
HAND_6 = 0x0004
SPARE_1 = 0x00400000
SPARE_2 = 0x00800000

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

MESSAGE_LENGTH = 16


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["BLACK_B"] = BLACK_B
    DISPLAY_MAPS["BLACK_L"] = BLACK_L
    DISPLAY_MAPS["BLACK_A"] = BLACK_A
    DISPLAY_MAPS["BLACK_C"] = BLACK_C
    DISPLAY_MAPS["BLACK_K"] = BLACK_K
    DISPLAY_MAPS["BLACK"] = BLACK_B | BLACK_L | BLACK_A | BLACK_C | BLACK_K
    DISPLAY_MAPS["LIVES_L"] = LIVES_L
    DISPLAY_MAPS["LIVES_I"] = LIVES_I
    DISPLAY_MAPS["LIVES_V"] = LIVES_V
    DISPLAY_MAPS["LIVES_E"] = LIVES_E
    DISPLAY_MAPS["LIVES_S"] = LIVES_S
    DISPLAY_MAPS["LIVES"] = LIVES_L | LIVES_I | LIVES_V | LIVES_E | LIVES_S
    DISPLAY_MAPS["MATTER_M"] = MATTER_M
    DISPLAY_MAPS["MATTER_A"] = MATTER_A
    DISPLAY_MAPS["MATTER_T1"] = MATTER_T1
    DISPLAY_MAPS["MATTER_T2"] = MATTER_T2
    DISPLAY_MAPS["MATTER_E"] = MATTER_E
    DISPLAY_MAPS["MATTER_R"] = MATTER_R
    DISPLAY_MAPS["MATTER"] = (
        MATTER_M | MATTER_A | MATTER_T1 | MATTER_T2 | MATTER_E | MATTER_R
    )
    DISPLAY_MAPS["FULL"] = BLACK | LIVES | MATTER
    DISPLAY_MAPS["HAND_1"] = HAND_1
    DISPLAY_MAPS["HAND_2"] = HAND_2
    DISPLAY_MAPS["HAND_3"] = HAND_3
    DISPLAY_MAPS["HAND_4"] = HAND_4
    DISPLAY_MAPS["HAND_5"] = HAND_5
    DISPLAY_MAPS["HAND_6"] = HAND_6
    DISPLAY_MAPS["ALL_HANDS"] = HAND_1 | HAND_2 | HAND_3 | HAND_4 | HAND_5 | HAND_6
    DISPLAY_MAPS["SPARE_1"] = SPARE_1
    DISPLAY_MAPS["SPARE_2"] = SPARE_2


def first_then_scroll():
    """ First letter then full """
    display = BLACK_B | LIVES_L | MATTER_M
    for _ in range(0, int(TIMES)):
        push_data(display)
        time.sleep(SLOW)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(SLOW)
    clear()


def one_at_a_time():
    """ One at a time """
    for _ in range(0, int(TIMES)):
        push_data(DISPLAY_MAPS["BLACK"])
        time.sleep(MEDIUM)
        push_data(DISPLAY_MAPS["LIVES"])
        time.sleep(MEDIUM)
        push_data(DISPLAY_MAPS["MATTER"])
        time.sleep(MEDIUM)
    clear()


def window(first_on: bool = False):
    """ Slide window across """
    display = BLACK_B | LIVES_L | MATTER_M if first_on else 0
    for _ in range(0, int(TIMES)):
        bit = 0
        for j in range(0, MESSAGE_LENGTH):
            bit = bit | 0x1 << j
            push_data(bit | display)
            time.sleep(FAST)
        for j in range(0, MESSAGE_LENGTH):
            bit = 0xFFFF & (0xFFFF << (j + 1))
            push_data(bit | display)
            time.sleep(FAST)
    clear()


def window_words(first_on: bool = False):
    """ Slide window across each word """

    def overlay_on_words():
        black = (DISPLAY_MAPS["BLACK"] & bit) | (BLACK_B if first_on else 0)
        lives = (DISPLAY_MAPS["LIVES"] & (bit << 5)) | (LIVES_L if first_on else 0)
        matter = (DISPLAY_MAPS["MATTER"] & (bit << 10)) | (MATTER_M if first_on else 0)
        push_data(black | lives | matter)
        time.sleep(FAST)

    for _ in range(0, int(TIMES)):
        bit = 0
        for j in range(0, MESSAGE_LENGTH):
            bit = bit | 0x1 << j
            overlay_on_words()
        for j in range(0, MESSAGE_LENGTH):
            bit = 0xFFFF << (j + 1)
            overlay_on_words()
    clear()


def hand_clasp():
    """ Animate the hand clasp """
    for _ in range(0, int(TIMES)):
        push_data(DISPLAY_MAPS["FULL"], HAND_1 | HAND_6)
        time.sleep(SLOW - 0.25)
        push_data(DISPLAY_MAPS["FULL"], HAND_1 | HAND_6 | HAND_2 | HAND_5)
        time.sleep(SLOW - 0.25)
        push_data(DISPLAY_MAPS["FULL"], DISPLAY_MAPS["ALL_HANDS"])
        time.sleep(5)
    clear()


window_first_on = partial(window, first_on=True)
window_words_first_on = partial(window_words, first_on=True)

ANIMATION_ORDER = {
    1: startup,
    2: window,
    3: startup_shutdown,
    4: first_then_scroll,
    5: scroll,
    6: window_words_first_on,
    7: one_at_a_time,
    8: window_first_on,
    9: scroll,
    10: startup_shutdown,
    11: window_words,
    12: first_then_scroll,
}
