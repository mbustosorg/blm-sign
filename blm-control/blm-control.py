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
import time
from logging.handlers import RotatingFileHandler

import smbus
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('blm-sign')
logger.setLevel(logging.INFO)
log_format = logging.Formatter(FORMAT)

file_handler = RotatingFileHandler('blm-control.log', maxBytes=20000, backupCount=10)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

BLACK_B = 0x0001
BLACK_L = 0x0002
BLACK_A = 0x0004
BLACK_C = 0x0008
BLACK_K = 0x0010
LIVES_L = 0x0020
LIVES_I = 0x0040
LIVES_V = 0x0080
LIVES_E = 0x0100
LIVES_S = 0x0200
MATTER_M = 0x0400
MATTER_A = 0x0800
MATTER_T1 = 0x1000
MATTER_T2 = 0x2000
MATTER_E = 0x4000
MATTER_R = 0x8000

DISPLAY_MAPS = {
    "BLACK_B": BLACK_B,
    "BLACK_L": BLACK_L,
    "BLACK_A": BLACK_A,
    "BLACK_C": BLACK_C,
    "BLACK_K": BLACK_K,
    "BLACK": BLACK_B | BLACK_L | BLACK_A | BLACK_C | BLACK_K,
    "LIVES_L": LIVES_L,
    "LIVES_I": LIVES_I,
    "LIVES_V": LIVES_V,
    "LIVES_E": LIVES_E,
    "LIVES_S": LIVES_S,
    "LIVES": LIVES_L | LIVES_I | LIVES_V | LIVES_E | LIVES_S,
    "MATTER_M": MATTER_M,
    "MATTER_A": MATTER_A,
    "MATTER_T1": MATTER_T1,
    "MATTER_T2": MATTER_T2,
    "MATTER_E": MATTER_E,
    "MATTER_R": MATTER_R,
    "MATTER": MATTER_M | MATTER_A | MATTER_T1 | MATTER_T2 | MATTER_E | MATTER_R
}

DEVICE = 0x27
IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

bus = smbus.SMBus(1)

bus.write_byte_data(DEVICE, IODIRA, 0x00)
bus.write_byte_data(DEVICE, IODIRB, 0x00)
bus.write_byte_data(DEVICE, OLATA, 0)
bus.write_byte_data(DEVICE, OLATB, 0)

current_display = 0x0000
queue = []


def handle_letter(path: str, value):
    """ Toggle letter commanded """
    global current_display

    letter = path.split('/')[2]
    display_map = DISPLAY_MAPS[letter]
    current_display = current_display ^ display_map

    bus.write_byte_data(DEVICE, OLATA, current_display)
    bus.write_byte_data(DEVICE, OLATB, current_display >> 8)

    logger.info(f'{path} {bin(current_display)}')


def handle_word(path: str, value):
    """ Toggle word commanded """
    global current_display

    word = path.split('/')[2]
    display_map = DISPLAY_MAPS[word]
    if current_display & display_map == 0:
        current_display = current_display | display_map
    elif current_display & display_map == display_map:
        current_display = current_display & ~display_map
    else:
        current_display = current_display | display_map

    bus.write_byte_data(DEVICE, OLATA, current_display)
    bus.write_byte_data(DEVICE, OLATB, current_display >> 8)

    logger.info(f'{path} {bin(current_display)}')


def handle_full(path: str, value):
    """ Toggle full display """
    global current_display

    if current_display == 0xFFFF:
        current_display = 0x0000
    else:
        current_display = 0xFFFF

    bus.write_byte_data(DEVICE, OLATA, current_display)
    bus.write_byte_data(DEVICE, OLATB, current_display >> 8)

    logger.info(f'{path} {bin(current_display)}')


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    global current_display

    logger.info(path)
    queue.append(int(path.split('/')[2]))


async def run_command(number):
    """ Run 'command' """
    time.sleep(number)
    logger.info(f'{number} complete')


async def main_loop():
    """ Main execution loop """
    while True:
        if len(queue) > 0:
            logger.info(f'{len(queue)} commands in the queue')
            await asyncio.create_task(run_command(queue.pop(0)))
        await asyncio.sleep(1)


async def init_main(args, dispatcher):
    """ Initialization routine """
    loop = asyncio.get_event_loop()
    server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, loop)
    transport, protocol = await server.create_serve_endpoint()

    await main_loop()

    transport.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="10.0.1.47", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=9999, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.map('/letter/*', handle_letter)
    dispatcher.map('/word/*', handle_word)
    dispatcher.map('/full', handle_full)
    dispatcher.map('/animation/*', handle_animation)

    logger.info(f'Serving on {args.ip}:{args.port}')

    asyncio.run(init_main(args, dispatcher))
