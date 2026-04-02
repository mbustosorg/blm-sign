"""
Copyright (C) 2025 Mauricio Bustos (m@bustos.org)
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
import time

from blmcontrol.animation_utils import (
    TIMES,
    MEDIUM,
    FAST,
    clear,
    window,
    scroll,
    startup,
    DISPLAY_MAPS,
    pwm,
    set_pwm,
    gamma,
    MAX_PWM,
)
import blmcontrol.animation_utils

MAX_PWM = 4000
ENABLE_WORDS = True
T_WHITE = 0x0004
T_PURPLE = 0x0008
HEART_RED =  0x0040
HEART_WHITE = 0x0040
R_WHITE = 0x0002
R_PURPLE = 0x0001
T = T_WHITE | T_PURPLE
R = R_WHITE | R_PURPLE
HEART = HEART_RED | HEART_WHITE
FIRST_COLOR = T_WHITE | HEART_WHITE | R_WHITE
SECOND_COLOR = T_PURPLE | HEART_RED | R_PURPLE

blmcontrol.animation_utils.MESSAGE_LENGTH = 5

LOGGER = logging.getLogger("blm-sign")


def push_data(value, instant=True, descending=False, ascending=False, steps=80):
    """ Push data to I2C devices """
    try_count = 4
    if instant:
        steps = [MAX_PWM]
    elif descending:
        steps = list(map(lambda x: MAX_PWM - float(x) / float(steps) * float(MAX_PWM), range(steps)))
    elif ascending:
        steps = list(map(lambda x: float(x) / float(steps) * float(MAX_PWM), range(steps)))
    for step in steps:
        for i in range(8):
            for j in range(try_count):
                try:
                    if value & 1 << i:
                        blmcontrol.animation_utils.pwm.set_pwm(i, 0, gamma(int(step)))
                    else:
                        blmcontrol.animation_utils.pwm.set_pwm(i, 0, 0)
                    break
                except Exception as e:
                    if j < try_count:
                        LOGGER.error(f"Exception during 'set_pwm', try again: {str(e)}, i={i}, j={j}, step={step}, value={value}")
                        continue
                    LOGGER.error(f"Too many failures during 'set_pwm' {str(e)}, i={i}, step={step}, value={value}")
                    raise e


def set_display_maps():
    """Update the DISPLAY_MAPS variable"""
    DISPLAY_MAPS["T_WHITE"] = T_WHITE
    DISPLAY_MAPS["T_PURPLE"] = T_PURPLE
    DISPLAY_MAPS["HEART_RED"] = HEART_RED
    DISPLAY_MAPS["HEART_WHITE"] = HEART_WHITE
    DISPLAY_MAPS["R_WHITE"] = R_WHITE
    DISPLAY_MAPS["R_PURPLE"] = R_PURPLE
    DISPLAY_MAPS["T"] = T
    DISPLAY_MAPS["R"] = R
    DISPLAY_MAPS["FIRST_COLOR"] = FIRST_COLOR
    DISPLAY_MAPS["SECOND_COLOR"] = SECOND_COLOR
    DISPLAY_MAPS["FULL"] = T | HEART | R
    DISPLAY_MAPS["HEART"] = HEART_RED | HEART_WHITE


def sequence_through():
    """Sequence through full"""
    delay = FAST
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["T"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["T"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["HEART"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["HEART"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["R"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["R"], instant=False, descending=True)
        push_data(0)
        time.sleep(delay)
    clear()


def sequence_through_full():
    """Sequence through every light"""
    delay = FAST
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["T_WHITE"])
        push_data(DISPLAY_MAPS["T_WHITE"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["T_PURPLE"])
        push_data(DISPLAY_MAPS["T_PURPLE"], instant=False, descending=True)
        time.sleep(delay)
        push_data(DISPLAY_MAPS["HEART_RED"])
        push_data(DISPLAY_MAPS["HEART_RED"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["HEART_WHITE"])
        push_data(DISPLAY_MAPS["HEART_WHITE"], instant=False, descending=True)
        time.sleep(delay)
        push_data(DISPLAY_MAPS["R_WHITE"])
        push_data(DISPLAY_MAPS["R_WHITE"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["R_PURPLE"])
        push_data(DISPLAY_MAPS["R_PURPLE"], instant=False, descending=True)
        time.sleep(delay)
        push_data(0)
        time.sleep(delay)
    clear()


def color_cycle_up_down():
    """Cycle through the colors at once"""
    delay = FAST
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["FIRST_COLOR"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["FIRST_COLOR"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["SECOND_COLOR"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["SECOND_COLOR"], instant=False, descending=True)
        time.sleep(delay)
        push_data(0)
        time.sleep(delay)
    clear()


def color_cycle():
    """Cycle through the colors at once up and down"""
    delay = FAST
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["FIRST_COLOR"])
        push_data(DISPLAY_MAPS["FIRST_COLOR"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["SECOND_COLOR"])
        push_data(DISPLAY_MAPS["SECOND_COLOR"], instant=False, descending=True)
        time.sleep(delay)
        push_data(0)
        time.sleep(delay)
    clear()


ANIMATION_ORDER = {
    1: sequence_through,
    2: sequence_through_full,
    3: color_cycle_up_down,
    4: color_cycle,
    5: sequence_through,
    6: sequence_through_full,
}
