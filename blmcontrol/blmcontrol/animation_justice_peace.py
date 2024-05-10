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
import logging
import time

from blmcontrol.animation_utils import (
    TIMES,
    MEDIUM,
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

ENABLE_WORDS = True
KW_1 = 0x0080
NO_1 = 0x0040
JUS =  0x0020
TICE = 0x0010
KW_2 = 0x0008
NO_2 = 0x0004
PEA =  0x0002
CE =   0x0001
FULL = 0x00FF
NO_JP = NO_1 | JUS | TICE | NO_2 | PEA | CE
KNOW_JP = KW_1 | NO_1 | JUS | TICE | KW_2 | NO_2 | PEA | CE

FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12

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
    DISPLAY_MAPS["KW_1"] = KW_1
    DISPLAY_MAPS["NO_1"] = NO_1
    DISPLAY_MAPS["KNOW_1"] = KW_1 | NO_1
    DISPLAY_MAPS["JUS"] = JUS
    DISPLAY_MAPS["TICE"] = TICE
    DISPLAY_MAPS["JUSTICE"] = JUS | TICE
    DISPLAY_MAPS["KW_2"] = KW_2
    DISPLAY_MAPS["NO_2"] = NO_2
    DISPLAY_MAPS["KNOW_2"] = KW_2 | NO_2
    DISPLAY_MAPS["PEA"] = PEA
    DISPLAY_MAPS["CE"] = CE
    DISPLAY_MAPS["PEACE"] = PEA | CE
    DISPLAY_MAPS["NO_JP"] = NO_JP
    DISPLAY_MAPS["KNOW_JP"] = KNOW_JP
    DISPLAY_MAPS["FULL"] = FULL


def know():
    """Use KNOW"""
    delay = MEDIUM / 4
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["KNOW_1"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_1"], instant=False, descending=True, steps=20)
        push_data(DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["JUSTICE"], instant=False, descending=True, steps=20)
        push_data(0)
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_2"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_2"], instant=False, descending=True, steps=20)
        push_data(DISPLAY_MAPS["PEACE"])
        time.sleep(delay * 1.5)
        push_data(DISPLAY_MAPS["PEACE"], instant=False, descending=True, steps=20)
        push_data(0)
        time.sleep(delay)
    clear()


def no():
    """Use NO"""
    delay = MEDIUM / 2
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["NO_1"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["NO_1"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_1"], instant=False, descending=True, steps=20)
        push_data(DISPLAY_MAPS["JUSTICE"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["JUSTICE"], instant=False, descending=True, steps=20)
        push_data(0)
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_2"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["NO_2"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_2"], instant=False, descending=True, steps=20)
        push_data(DISPLAY_MAPS["PEACE"], instant=False, ascending=True, steps=5)
        push_data(DISPLAY_MAPS["PEACE"])
        time.sleep(delay * 1.5)
        push_data(DISPLAY_MAPS["PEACE"], instant=False, descending=True, steps=20)
        push_data(0)
        time.sleep(delay)
    clear()


def toggle():
    """Toggle between two messages"""
    delay = MEDIUM
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["NO_JP"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_JP"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["FULL"])
        time.sleep(delay)
    clear()


def sequence_through():
    """Toggle between two messages"""
    delay = MEDIUM
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["KNOW_1"] | DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_1"] | DISPLAY_MAPS["JUSTICE"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["KNOW_2"] | DISPLAY_MAPS["PEACE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_2"] | DISPLAY_MAPS["PEACE"], instant=False, descending=True)
        push_data(0)
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_1"] | DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_1"] | DISPLAY_MAPS["JUSTICE"], instant=False, descending=True)
        push_data(DISPLAY_MAPS["NO_2"] | DISPLAY_MAPS["PEACE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_2"] | DISPLAY_MAPS["PEACE"], instant=False, descending=True)
        push_data(0)
        time.sleep(delay)
    clear()


def diagonal():
    """Diagonal between two messages"""
    delay = 2.0
    for _ in range(0, int(TIMES / 3)):
        push_data(DISPLAY_MAPS["KNOW_2"] | DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["KNOW_1"] | DISPLAY_MAPS["PEACE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_2"] | DISPLAY_MAPS["JUSTICE"])
        time.sleep(delay)
        push_data(DISPLAY_MAPS["NO_1"] | DISPLAY_MAPS["PEACE"])
        time.sleep(delay)
        push_data(0)
    time.sleep(delay)
    clear()
    time.sleep(5.0)


def pj():
    """Just Peace and Justice"""
    push_data(DISPLAY_MAPS["PEACE"] | DISPLAY_MAPS["JUSTICE"])
    time.sleep(20)
    clear()
    time.sleep(5.0)


ANIMATION_ORDER = {
    #1: clear,
    #2: clear,
    #3: clear,
    #4: clear,
    #5: clear,
    #6: clear,
    1: no,
    2: know,
    3: toggle,
    4: sequence_through,
    5: diagonal,
    6: pj,
}
