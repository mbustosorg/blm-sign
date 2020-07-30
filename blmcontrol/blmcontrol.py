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

import argparse
import asyncio
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from typing import List, Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from yoctopuce.yocto_watchdog import *
from animations import *
import earth_data

try:
    import RPi.GPIO as GPIO
    RPI = True
except ImportError:
    RPI = False


FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER: Logger = logging.getLogger('blm-sign')
LOGGER.setLevel(logging.INFO)
LOG_FORMAT = logging.Formatter(FORMAT)

FILE_HANDLER = RotatingFileHandler('blmcontrol.log', maxBytes=40000, backupCount=5)
FILE_HANDLER.setLevel(logging.INFO)
FILE_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(FILE_HANDLER)

CURRENT_DISPLAY = 0x0000
QUEUE = []
WATCHDOG = None


def handle_parameter(path: str, value):
    """ Handle a parameter change """
    set_timing(path.split('/')[2], value)


def handle_letter(path: str, value: List[Any]):
    """ Toggle letter commanded """
    global CURRENT_DISPLAY
    del value

    letter = path.split('/')[2]
    display_map = DISPLAY_MAPS[letter]
    CURRENT_DISPLAY = CURRENT_DISPLAY ^ display_map

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'{path} {bin(CURRENT_DISPLAY)}')


def handle_word(path: str, value):
    """ Toggle word commanded """
    global CURRENT_DISPLAY
    del value

    word = path.split('/')[2]
    display_map = DISPLAY_MAPS[word]
    if CURRENT_DISPLAY & display_map == 0:
        CURRENT_DISPLAY = CURRENT_DISPLAY | display_map
    elif CURRENT_DISPLAY & display_map == display_map:
        CURRENT_DISPLAY = CURRENT_DISPLAY & ~display_map
    else:
        CURRENT_DISPLAY = CURRENT_DISPLAY | display_map

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'{path} {bin(CURRENT_DISPLAY)}')


def handle_full(path: str = None, value=None):
    """ Toggle full display """
    global CURRENT_DISPLAY
    del value

    if CURRENT_DISPLAY == 0xFFFF:
        CURRENT_DISPLAY = 0x0000
    else:
        CURRENT_DISPLAY = 0xFFFF

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'handle full: {path} {bin(CURRENT_DISPLAY)}')


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    del value

    LOGGER.info(f'Received {path}')
    QUEUE.append(int(path.split('/')[2]))


async def run_command(number):
    """ Run 'command' """
    global CURRENT_DISPLAY

    LOGGER.info(f'Starting {number}')
    if number == 1:
        first_then_scroll()
    elif number == 2:
        one_at_a_time()
    elif number == 3:
        window()
    elif number == 4:
        random_letters()
    elif number == 5:
        scroll()
    elif number == 6:
        flickering()
    elif number == 7:
        startup()
    LOGGER.info(f'{number} complete')
    CURRENT_DISPLAY = 0
    handle_full()


async def main_loop(start_time_string, end_time_string, animate):
    """ Main execution loop """
    global QUEUE, CURRENT_DISPLAY

    last_request = datetime.datetime.utcnow()
    current_animation = 0

    while True:
        now = datetime.datetime.utcnow()
        if len(QUEUE) > 0:
            last_request = now
            if QUEUE[-1] == 8:
                QUEUE = []
                LOGGER.info(f'Cancel commanded, resetting')
            else:
                LOGGER.info(f'{len(QUEUE)} commands in the queue')
                await asyncio.create_task(run_command(QUEUE.pop(0)))
        if (now - last_request).seconds > animate + 60:
            if earth_data.lights_out(on_offset=120, hard_off=end_time_string):
                if CURRENT_DISPLAY != 0:
                    LOGGER.info('Shutting down')
                    CURRENT_DISPLAY = 0
                    push_data(CURRENT_DISPLAY)
            else:
                if CURRENT_DISPLAY != 0xFFFF:
                    LOGGER.info('Starting up')
                    CURRENT_DISPLAY = 0xFFFF
                    push_data(CURRENT_DISPLAY)
        if animate:
            if (now - last_request).seconds > animate:
                current_animation += 1
                if current_animation > 7:
                    current_animation = 1
                last_request = now
                handle_animation(f'/animation/{current_animation}', None)
        await asyncio.sleep(1)
        if WATCHDOG:
            WATCHDOG.resetWatchdog()


def signal(length, count):
    """ Signal status on buzzer """
    if RPI:
        for j in range(0, count):
            GPIO.output(12, True)
            time.sleep(length)
            GPIO.output(12, False)
            time.sleep(length)


async def init_main(args, dispatcher):
    """ Initialization routine """
    loop = asyncio.get_event_loop()
    for i in range(0, 5):
        try:
            server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, loop)
            LOGGER.info(f'Serving on {args.ip}:{args.port}')
            signal(0.05, 3)
            break
        except:
            signal(0.5, 3)
            LOGGER.warning(f'Unable to bind to {args.ip}, retrying {i + 1}')
            time.sleep(3)

    for i in range(0, 5):
        try:
            transport, _ = await server.create_serve_endpoint()
            LOGGER.info(f'Server endpoint established')
            signal(0.05, 3)
            break
        except:
            signal(0.5, 3)
            LOGGER.warning('Unable to establish endpoint, retrying')
            time.sleep(5)

    await main_loop(args.start_time, args.end_time, args.animate)

    transport.close()


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('--ip', default='10.0.1.47', help='The ip to listen on')
    PARSER.add_argument('--port', type=int, default=9999, help='The port to listen on')
    PARSER.add_argument('--start_time', type=str, default='3:00', help='start time')
    PARSER.add_argument('--end_time', type=str, default='8:00', help='end time')
    PARSER.add_argument('--animate', type=int, default=0, help='animation period')
    ARGS = PARSER.parse_args()

    ERRMSG = YRefParam()
    if YAPI.RegisterHub('usb', ERRMSG) != YAPI.SUCCESS:
        LOGGER.error(f'YAPI init error {ERRMSG.value}')
    else:
        WATCHDOG = YWatchdog.FirstWatchdog()
        if WATCHDOG:
            WATCHDOG.resetWatchdog()
        else:
            LOGGER.error('No watchdog connected')

    DISPATCHER = Dispatcher()
    DISPATCHER.map('/letter/*', handle_letter)
    DISPATCHER.map('/word/*', handle_word)
    DISPATCHER.map('/full', handle_full)
    DISPATCHER.map('/animation/*', handle_animation)
    DISPATCHER.map('/parameter/*', handle_parameter)

    if RPI:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12, GPIO.OUT)
        signal(0.25, 2)

    handle_full('', None)

    asyncio.run(init_main(ARGS, DISPATCHER))
