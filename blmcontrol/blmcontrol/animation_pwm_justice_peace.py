"""
    Copyright (C) 2024 Mauricio Bustos (m@bustos.org)
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

pwm = None


def set_pwm(pwm_driver):
    """Set local pwm driver"""
    global pwm
    pwm = pwm_driver


def gamma(original, correction=0.4):
    """ Gamma correction for LED strips """
    return int(((original / 4096.0) ** (1 / correction)) * 4096)


def cycle():
    """Up and down"""
    level = [0, 0, 0, 0, 0, 0, 0, 0]
    pattern_index = [0, 0, 0, 0, 0, 0, 0, 0]
    direction = [1, 1, 1, 1, 1, 1, 1, 1]
    pattern = [1, -1]
    for _ in range(1000):
        for i in range(8):
            level[i] = level[i] + direction[i] * 20
            if level[i] >= 4096:
                level[i] = 4095
                pattern_index[i] = pattern_index[i] + 1
                if pattern_index[i] >= len(pattern):
                    pattern_index[i] = 0
                direction[i] = pattern[pattern_index[i]]
            elif level[i] < 0:
                level[i] = 0
                pattern_index[i] = pattern_index[i] + 1
                if pattern_index[i] >= len(pattern):
                    pattern_index[i] = 0
                direction[i] = pattern[pattern_index[i]]
            pwm.set_pwm(i, 0, gamma(int(level[i])))


def snake():
    """One end to the other"""
    step = 4096 / 8
    level = [0, step, step * 2, step * 3, step * 4, step * 5, step * 6, step * 7]
    pattern_index = [0, 0, 0, 0, 0, 0, 0, 0]
    direction = [1, 1, 1, 1, 1, 1, 1, 1]
    pattern = [1, -1]
    for _ in range(1000):
        for i in range(8):
            level[i] = level[i] + direction[i] * 20
            if level[i] >= 4096:
                level[i] = 4095
                pattern_index[i] = pattern_index[i] + 1
                if pattern_index[i] >= len(pattern):
                    pattern_index[i] = 0
                direction[i] = pattern[pattern_index[i]]
            elif level[i] < 0:
                level[i] = 0
                pattern_index[i] = pattern_index[i] + 1
                if pattern_index[i] >= len(pattern):
                    pattern_index[i] = 0
                direction[i] = pattern[pattern_index[i]]
            pwm.set_pwm(i, 0, gamma(int(level[i])))


ANIMATION_ORDER = {
    1: cycle,
    2: snake,
}
