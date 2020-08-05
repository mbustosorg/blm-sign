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
from unittest import TestCase

import blmcontrol.earth_data as ed
import datetime


class TestEarthData(TestCase):

    def test_sun(self):
        """ Ensure able to get solar data """
        now = datetime.datetime.now().replace(hour=12)
        self.assertTrue(ed.lights_out(now))
        now = datetime.datetime.now().replace(hour=1)
        self.assertFalse(ed.lights_out(current_time=now, hard_off='2:30'))