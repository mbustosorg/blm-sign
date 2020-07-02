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
from blmcontrol.animations import *


FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER: Logger = logging.getLogger('blm-sign')
LOGGER.setLevel(logging.INFO)
LOG_FORMAT = logging.Formatter(FORMAT)

FILE_HANDLER = RotatingFileHandler('blmcontrol.log', maxBytes=20000, backupCount=10)
FILE_HANDLER.setLevel(logging.INFO)
FILE_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(FILE_HANDLER)

CURRENT_DISPLAY = 0x0000
QUEUE = []
WATCHDOG = None


def handle_letter(path: str, value: List[Any]):
    """ Toggle letter commanded """
    global CURRENT_DISPLAY
    del value

    letter = path.split('/')[2]
    display_map = DISPLAY_MAPS[letter]
    CURRENT_DISPLAY = CURRENT_DISPLAY ^ display_map

    BUS.write_byte_data(DEVICE1, OLATA, CURRENT_DISPLAY)
    BUS.write_byte_data(DEVICE1, OLATB, CURRENT_DISPLAY >> 8)

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

    BUS.write_byte_data(DEVICE1, OLATA, CURRENT_DISPLAY)
    BUS.write_byte_data(DEVICE1, OLATB, CURRENT_DISPLAY >> 8)

    LOGGER.info(f'{path} {bin(CURRENT_DISPLAY)}')


def handle_full(path: str, value):
    """ Toggle full display """
    global CURRENT_DISPLAY
    del value

    if CURRENT_DISPLAY == 0xFFFF:
        CURRENT_DISPLAY = 0x0000
    else:
        CURRENT_DISPLAY = 0xFFFF

    BUS.write_byte_data(DEVICE1, OLATA, CURRENT_DISPLAY)
    BUS.write_byte_data(DEVICE1, OLATB, CURRENT_DISPLAY >> 8)

    LOGGER.info(f'{path} {bin(CURRENT_DISPLAY)}')


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    global CURRENT_DISPLAY
    del value

    LOGGER.info(path)
    QUEUE.append(int(path.split('/')[2]))


async def run_command(number):
    """ Run 'command' """
    if number == 1:
        blm_then_scroll()
    elif number == 2:
        black_lives_matter()
    elif number == 3:
        scroll()
    LOGGER.info(f'{number} complete')


async def main_loop():
    """ Main execution loop """
    while True:
        if len(QUEUE) > 0:
            LOGGER.info(f'{len(QUEUE)} commands in the queue')
            await asyncio.create_task(run_command(QUEUE.pop(0)))
        await asyncio.sleep(1)
        if WATCHDOG:
            WATCHDOG.resetWatchdog()


async def init_main(args, dispatcher):
    """ Initialization routine """
    loop = asyncio.get_event_loop()
    server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, loop)
    transport, _ = await server.create_serve_endpoint()

    await main_loop()

    transport.close()


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--ip", default="10.0.1.47", help="The ip to listen on")
    PARSER.add_argument("--port", type=int, default=9999, help="The port to listen on")
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

    LOGGER.info(f'Serving on {ARGS.ip}:{ARGS.port}')

    asyncio.run(init_main(ARGS, DISPATCHER))
