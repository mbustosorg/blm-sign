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

import argparse
import asyncio
import logging
import time
import datetime
from logging import Logger
from functools import partial
from logging.handlers import RotatingFileHandler

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

from blmcontrol.PCA9685 import PCA9685
from blmcontrol.animation_utils import animate_interval, set_signal, signal, check_cell_connectivity, broadcast_message
from blmcontrol.animation_justice_peace import ANIMATION_ORDER, set_display_maps, set_pwm, clear, push_data


FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
LOGGER: Logger = logging.getLogger("blm-sign")
LOGGER.setLevel(logging.INFO)
LOG_FORMAT = logging.Formatter(FORMAT)

FILE_HANDLER = RotatingFileHandler("pwmcontrol.log", maxBytes=200000, backupCount=5)
FILE_HANDLER.setLevel(logging.INFO)
FILE_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(FILE_HANDLER)

FORMAT = "%(asctime)-15s|%(module)s|%(lineno)d|%(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

pwm = PCA9685(logger=logger)

BPM = 120.0
PERIOD = 1.0 / BPM * 60.0 * 1000.0
STEP = 4096
UPPER = 4000
STEP = 5

pwm.set_pwm_freq(200)
set_pwm(pwm)

current_display = 0x0000
ANIMATIONS = "animations"
LAST_REQUEST = "last_request"
CURRENT_ANIMATION = "current_animation"
QUEUE = {ANIMATIONS: [], LAST_REQUEST: datetime.datetime.now(), CURRENT_ANIMATION: 1}
SIGNAL = True


def handle_bpm(unused_addr, args):
    """ Handle the BPM value update """
    global BPM, PERIOD
    try:
        logger.info(f'[{int(args)}]')
        BPM = float(int(args))
        PERIOD = 1.0 / BPM * 60.0 * 1000.0
    except ValueError as e:
        logger.error(e)
    msg = osc_message_builder.OscMessageBuilder(address="/bpm_feedback")
    msg.add_arg(int(BPM))
    built = msg.build()
    mobile_client.send(built)


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    del value

    LOGGER.info(f"Received {path}")
    QUEUE[ANIMATIONS].append(int(path.split("/")[2]))
    QUEUE[LAST_REQUEST] = datetime.datetime.now()


async def run_command(number):
    """ Run 'command' """
    global current_display

    function = ANIMATION_ORDER[number]
    if isinstance(function, partial):
        LOGGER.info(
            f"Starting {number} - {function.func.__name__} {str(function.keywords)}"
        )
    else:
        LOGGER.info(f"Starting {number} - {function.__name__}")
    function()
    LOGGER.info(f"{number} complete")
    current_display = 0


async def main_loop(args):
    """ Main execution loop """
    global current_display, QUEUE

    is_stopped = True
    broadcast_message("KJKP application starting")

    QUEUE[LAST_REQUEST] = datetime.datetime.now()
    handle_animation(f"/animation/{QUEUE[CURRENT_ANIMATION]}", None)

    check_cell_connectivity()

    while True:
        date = datetime.datetime.now()
        if date.weekday() > 4:
            if not is_stopped:
                is_stopped = True
                broadcast_message("KJKP shutting off")
            push_data(0)
            check_cell_connectivity()
            await asyncio.sleep(300)
            continue
        elif date.weekday() == 1 and (date.hour < 9 or date.hour > 23):
            if not is_stopped:
                is_stopped = True
                broadcast_message("KJKP shutting off")
            push_data(0)
            check_cell_connectivity()
            await asyncio.sleep(300)
            continue
        elif date.hour < 9 or date.hour > 20:
            if not is_stopped:
                is_stopped = True
                broadcast_message("KJKP shutting off")
            push_data(0)
            check_cell_connectivity()
            await asyncio.sleep(300)
            continue
        if len(QUEUE[ANIMATIONS]) > 0:
            QUEUE[LAST_REQUEST] = datetime.datetime.now()
            if QUEUE[ANIMATIONS][-1] == max(ANIMATION_ORDER.keys()) + 1:
                QUEUE[ANIMATIONS] = []
                LOGGER.info(f"Cancel commanded, resetting")
            else:
                LOGGER.info(f"{len(QUEUE[ANIMATIONS])} commands in the queue")
                animation = QUEUE[ANIMATIONS].pop(0)
                await asyncio.create_task(run_command(animation))
                check_cell_connectivity()
        if (datetime.datetime.now() - QUEUE[LAST_REQUEST]).seconds > animate_interval(QUEUE[CURRENT_ANIMATION] - 1, args):
            if is_stopped:
                is_stopped = False
                broadcast_message("KJKP turning on")
            signal(0.05, 2)
            QUEUE[CURRENT_ANIMATION] += 1
            if QUEUE[CURRENT_ANIMATION] > max(ANIMATION_ORDER.keys()):
                QUEUE[CURRENT_ANIMATION] = 1
            QUEUE[LAST_REQUEST] = datetime.datetime.now()
            handle_animation(f"/animation/{QUEUE[CURRENT_ANIMATION]}", None)
        await asyncio.sleep(1)


async def init_main(args, dispatcher):
    """ Initialization routine """
    set_display_maps()
    clear()

    for i in range(0, 5):
        try:
            server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, asyncio.get_event_loop())
            transport, protocol = await server.create_serve_endpoint()
            LOGGER.info(f"Serving on {args.ip}:{args.port}")
            signal(0.05, 2)
            break
        except:
            signal(0.4, 2)
            LOGGER.warning(f"Unable to bind to {args.ip}, retrying {i + 1}")
            time.sleep(3)

    await main_loop(args)

    transport.close()


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--ip", default="10.0.0.103", help="The ip to listen on")
    PARSER.add_argument("--port", type=int, default=9999, help="The port to listen on")
    PARSER.add_argument('--mobile_ip', default='10.0.0.101',
                        help='The ip of the mobile osc display')
    PARSER.add_argument('--mobile_port', type=int, default=9999,
                        help='The port the mobile osc display is listening on')
    PARSER.add_argument('--signal', dest='signal', action='store_true')
    PARSER.add_argument('--no-signal', dest='signal', action='store_false')
    PARSER.add_argument(
        "--animate_intervals",
        type=int,
        nargs="+",
        help="list of seconds between intervals",
    )
    PARSER.set_defaults(feature=True)

    ARGS = PARSER.parse_args()
    mobile_client = udp_client.UDPClient(ARGS.mobile_ip, ARGS.mobile_port)

    DISPATCHER = Dispatcher()
    DISPATCHER.map("/bpm", handle_bpm)

    set_signal(ARGS)

    asyncio.run(init_main(ARGS, DISPATCHER))
