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
from unittest import TestCase

from mock import patch

import blmcontrol.earth_data.earth_data as ed


class TestEarthData(TestCase):
    @patch("blmcontrol.earth_data.earth_data.current_time")
    def test_sun(self, current_time_mock):
        """ Ensure able to get solar data """
        current_time_mock.return_value = datetime.datetime.now().replace(hour=12)
        self.assertTrue(ed.lights_out())
        current_time_mock.return_value = datetime.datetime.now().replace(hour=8)
        self.assertFalse(ed.lights_out(hard_off="10:30"))
