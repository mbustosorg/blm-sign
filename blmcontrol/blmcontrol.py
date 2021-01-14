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
from logging import Logger
from logging.handlers import RotatingFileHandler
from typing import List, Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from yoctopuce.yocto_watchdog import *
from blmcontrol.animations import *
from blmcontrol.earth_data import earth_data

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
ANIMATIONS = 'animations'
LAST_REQUEST = 'last_request'
CURRENT_ANIMATION = 'current_animation'
QUEUE = {ANIMATIONS: [],
         LAST_REQUEST: earth_data.current_time(),
         CURRENT_ANIMATION: 0}
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
    QUEUE[LAST_REQUEST] = earth_data.current_time()

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'{path}')


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
    QUEUE[LAST_REQUEST] = earth_data.current_time()

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'{path}')


def handle_full(path: str = None, value=None):
    """ Toggle full display """
    global CURRENT_DISPLAY
    del value

    if CURRENT_DISPLAY == 0xFFFFFFFF:
        CURRENT_DISPLAY = 0xFFFF0000
    else:
        CURRENT_DISPLAY = DISPLAY_MAPS['FULL'] << 16 | DISPLAY_MAPS['ALL_HANDS']
    QUEUE[LAST_REQUEST] = earth_data.current_time()

    push_data(CURRENT_DISPLAY)

    LOGGER.info(f'handle FULL')


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    del value

    LOGGER.info(f'Received {path}')
    QUEUE[ANIMATIONS].append(int(path.split('/')[2]))
    QUEUE[LAST_REQUEST] = earth_data.current_time()


async def run_command(number):
    """ Run 'command' """
    global CURRENT_DISPLAY

    LOGGER.info(f'Starting {number}')
    ANIMATION_ORDER[number]()
    LOGGER.info(f'{number} complete')
    CURRENT_DISPLAY = 0
    handle_full()


async def animation_control(on_offset, end_time_string, animate, current_request_delay=60):
    """ Iterate commands and handle on/off """
    global CURRENT_DISPLAY, QUEUE

    lights_are_out = earth_data.lights_out(on_offset=on_offset, hard_off=end_time_string)
    if len(QUEUE[ANIMATIONS]) > 0:
        QUEUE[LAST_REQUEST] = earth_data.current_time()
        if QUEUE[ANIMATIONS][-1] == max(ANIMATION_ORDER.keys()) + 1:
            QUEUE[ANIMATIONS] = []
            LOGGER.info(f'Cancel commanded, resetting')
        else:
            LOGGER.info(f"{len(QUEUE[ANIMATIONS])} commands in the queue")
            animation = QUEUE[ANIMATIONS].pop(0)
            await asyncio.create_task(run_command(animation))
#    if (earth_data.current_time() - QUEUE[LAST_REQUEST]).seconds > current_request_delay:
#        if lights_are_out:
#            if CURRENT_DISPLAY != 0:
#                QUEUE[ANIMATIONS] = []
#                LOGGER.info('Shutting down')
#                CURRENT_DISPLAY = 0
#                push_data(CURRENT_DISPLAY)
#        else:
#            if CURRENT_DISPLAY != 0xFFFF:
#                LOGGER.info('Starting up')
#                CURRENT_DISPLAY = 0xFFFF
#                push_data(CURRENT_DISPLAY)
    if (animate > 0) & (not lights_are_out):
        if (earth_data.current_time() - QUEUE[LAST_REQUEST]).seconds > animate:
            QUEUE[CURRENT_ANIMATION] += 1
            if QUEUE[CURRENT_ANIMATION] > max(ANIMATION_ORDER.keys()):
                QUEUE[CURRENT_ANIMATION] = 1
            QUEUE[LAST_REQUEST] = earth_data.current_time()
            handle_animation(f'/animation/{QUEUE[CURRENT_ANIMATION]}', None)
    else:
        if CURRENT_DISPLAY != 0:
            QUEUE[ANIMATIONS] = []
            LOGGER.info('Shutting down')
            CURRENT_DISPLAY = 0
            push_data(CURRENT_DISPLAY)
    await asyncio.sleep(1)
    if WATCHDOG:
        WATCHDOG.resetWatchdog()


async def main_loop(on_offset, end_time_string, animate):
    """ Main execution loop """
    while True:
        await animation_control(on_offset, end_time_string, animate)


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
        except Exception as e:
            signal(0.5, 3)
            LOGGER.warning('Unable to establish endpoint, retrying')
            time.sleep(5)

    await main_loop(args.on_offset, args.end_time, args.animate)

    transport.close()


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('--ip', default='10.0.1.47', help='The ip to listen on')
    PARSER.add_argument('--port', type=int, default=9999, help='The port to listen on')
    PARSER.add_argument('--on_offset', type=int, default=-120, help='minutes before sunset')
    PARSER.add_argument('--end_time', type=str, default='8:00', help='end time')
    PARSER.add_argument('--animate', type=int, default=30, help='animation period')
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
