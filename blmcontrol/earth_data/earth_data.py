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
import pandas as pd
import os
import datetime
from dateutil.relativedelta import relativedelta

SEVEN_HOURS = relativedelta(hours=7)
sun_data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'sunriseSunset.csv'), parse_dates=['sunrise', 'sunset'])
sun_data['sunrise'] = sun_data['sunrise']
sun_data['sunset'] = sun_data['sunset']
sun_data['date'] = sun_data['sunrise'].dt.date
sun_data = sun_data.set_index('date')


def current_time():
    """ Current UTC datetime """
    return datetime.datetime.utcnow()


def lights_out(time=None, on_offset: int = 0, hard_off: str = '10:00'):
    """ Are we off now? """
    if not time:
        time = current_time()
    now = time.replace(year=2000)
    off_time = datetime.datetime.strptime(hard_off, '%H:%M')
    off_time = off_time.replace(year=2000, day=now.day, month=now.month)
    if off_time.time() < now.time():
        off_time = off_time + relativedelta(days=1)
    on_delta = relativedelta(minutes=on_offset)
    on_time = sun_data.loc[now.date()]['sunset'] + on_delta
    if on_time > off_time:
        on_time = on_time - relativedelta(days=1)
    return not ((now >= on_time) & (now <= off_time))
