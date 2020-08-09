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
import asyncio
from unittest import TestCase
from mock import patch

import blmcontrol.earth_data.earth_data
import blmcontrol.blmcontrol
import blmcontrol.animations
import datetime


class TestAnimationOrder(TestCase):

    @patch('blmcontrol.earth_data.earth_data.current_time')
    def test_animation_start(self, current_time_mock):
        """ Check if animation starts on time """
        current_time_mock.return_value = datetime.datetime.now().replace(hour=12)
        self.assertTrue(blmcontrol.earth_data.earth_data.lights_out())
        current_time_mock.return_value = datetime.datetime.now().replace(hour=8)
        self.assertFalse(blmcontrol.earth_data.earth_data.lights_out(hard_off='10:30'))

    @patch('blmcontrol.earth_data.earth_data.current_time')
    def test_animation_select(self, current_time_mock):
        """ Check if animation starts correct one """
        blmcontrol.animations.TIMES = 1
        current_time_mock.return_value = datetime.datetime.now().replace(hour=10, minute=0)
        asyncio.run(blmcontrol.blmcontrol.animation_control(-120, '10:30', 10, 10))
        self.assertTrue(blmcontrol.blmcontrol.QUEUE['animations'] == [1])
        asyncio.run(blmcontrol.blmcontrol.animation_control(-120, '10:30', 10, 10))
        self.assertTrue(blmcontrol.blmcontrol.QUEUE['animations'] == [])
        current_time_mock.return_value = datetime.datetime.now().replace(hour=10, minute=15)
        asyncio.run(blmcontrol.blmcontrol.animation_control(-120, '10:30', 10, 10))
        self.assertTrue(blmcontrol.blmcontrol.QUEUE['animations'] == [2])
        asyncio.run(blmcontrol.blmcontrol.animation_control(-120, '10:30', 10, 10))
        self.assertTrue(blmcontrol.blmcontrol.QUEUE['animations'] == [])
        current_time_mock.return_value = datetime.datetime.now().replace(hour=12)
        asyncio.run(blmcontrol.blmcontrol.animation_control(-120, '10:30', 10, 10))
        self.assertEqual(blmcontrol.blmcontrol.CURRENT_DISPLAY, 0)
