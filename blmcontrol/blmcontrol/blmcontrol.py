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
# pylint: disable=logging-fstring-interpolation, f-string-without-interpolation
import argparse
import asyncio
import logging
import time
from functools import partial
from logging import Logger
from logging.handlers import RotatingFileHandler
from typing import List, Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from yoctopuce.yocto_watchdog import YAPI, YRefParam, YWatchdog
from blmcontrol.animation_utils import set_timing, push_data, DISPLAY_MAPS
#from blmcontrol.animations import ANIMATION_ORDER, set_display_maps
from blmcontrol.animation_patrick import ANIMATION_ORDER, set_display_maps

# from blmcontrol.animations_wedding import ANIMATION_ORDER, DISPLAY_MAPS

from blmcontrol.earth_data import earth_data

try:
    from RPi import GPIO

    RPI = True
except ImportError:
    RPI = False


FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
LOGGER: Logger = logging.getLogger("blm-sign")
LOGGER.setLevel(logging.INFO)
LOG_FORMAT = logging.Formatter(FORMAT)

FILE_HANDLER = RotatingFileHandler("blmcontrol.log", maxBytes=200000, backupCount=5)
FILE_HANDLER.setLevel(logging.INFO)
FILE_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(FILE_HANDLER)

current_display = 0x0000
ANIMATIONS = "animations"
LAST_REQUEST = "last_request"
CURRENT_ANIMATION = "current_animation"
QUEUE = {ANIMATIONS: [], LAST_REQUEST: earth_data.current_time(), CURRENT_ANIMATION: 0}
WATCHDOG = None


def handle_parameter(path: str, value):
    """ Handle a parameter change """
    set_timing(path.split("/")[2], value)


def handle_letter(path: str, value: List[Any]):
    """ Toggle letter commanded """
    global current_display
    del value

    letter = path.split("/")[2]
    display_map = DISPLAY_MAPS[letter]
    current_display = current_display ^ display_map
    QUEUE[LAST_REQUEST] = earth_data.current_time()

    push_data(current_display)

    LOGGER.info(f"{path}")


def handle_word(path: str, value):
    """ Toggle word commanded """
    global current_display
    del value

    word = path.split("/")[2]
    display_map = DISPLAY_MAPS[word]
    if current_display & display_map == 0:
        current_display = current_display | display_map
    elif current_display & display_map == display_map:
        current_display = current_display & ~display_map
    else:
        current_display = current_display | display_map
    QUEUE[LAST_REQUEST] = earth_data.current_time()

    push_data(current_display)

    LOGGER.info(f"{path}")


def handle_full(path: str = None, value=None):
    """ Toggle full display """
    global current_display
    del value, path

    current_display = 0xFFFFFFFF
    QUEUE[LAST_REQUEST] = earth_data.current_time()
    push_data(0xFFFFFFFF)


def handle_animation(path: str, value):
    """ Put an animation on the queue  """
    del value

    LOGGER.info(f"Received {path}")
    QUEUE[ANIMATIONS].append(int(path.split("/")[2]))
    QUEUE[LAST_REQUEST] = earth_data.current_time()


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
    handle_full()


async def main_loop(args):
    """ Main execution loop """
    global current_display, QUEUE
    set_display_maps()

    def animate_interval(index: int) -> int:
        """Next animation interval"""
        if args.animate_intervals:
            return args.animate_intervals[index]
        return args.animate

    while True:
        # push_data(0, 0)
        # await asyncio.sleep(1)
        # continue
        lights_are_out = False
        if args.enable_sun:
            lights_are_out = earth_data.lights_out(
                on_offset=args.on_offset, hard_off=args.end_time
            )
        if len(QUEUE[ANIMATIONS]) > 0:
            QUEUE[LAST_REQUEST] = earth_data.current_time()
            if QUEUE[ANIMATIONS][-1] == max(ANIMATION_ORDER.keys()) + 1:
                QUEUE[ANIMATIONS] = []
                LOGGER.info(f"Cancel commanded, resetting")
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
        if not lights_are_out:
            if (
                earth_data.current_time() - QUEUE[LAST_REQUEST]
            ).seconds > animate_interval(QUEUE[CURRENT_ANIMATION] - 1):
                signal(0.25, 2)
                QUEUE[CURRENT_ANIMATION] += 1
                if QUEUE[CURRENT_ANIMATION] > max(ANIMATION_ORDER.keys()):
                    QUEUE[CURRENT_ANIMATION] = 1
                QUEUE[LAST_REQUEST] = earth_data.current_time()
                handle_animation(f"/animation/{QUEUE[CURRENT_ANIMATION]}", None)
        else:
            if current_display != 0:
                QUEUE[ANIMATIONS] = []
                LOGGER.info("Shutting down for timing")
                current_display = 0
                push_data(current_display, 0)
        await asyncio.sleep(1)
        if WATCHDOG:
            WATCHDOG.resetWatchdog()


def signal(length, count):
    """ Signal status on buzzer """
    if RPI:
        for _ in range(0, count):
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
            LOGGER.info(f"Serving on {args.ip}:{args.port}")
            signal(0.05, 3)
            break
        except:
            signal(0.5, 3)
            LOGGER.warning(f"Unable to bind to {args.ip}, retrying {i + 1}")
            time.sleep(3)

    for i in range(0, 5):
        try:
            transport, _ = await server.create_serve_endpoint()
            LOGGER.info(f"Server endpoint established")
            signal(0.05, 3)
            break
        except Exception as _:
            signal(0.5, 3)
            LOGGER.warning("Unable to establish endpoint, retrying")
            time.sleep(5)

    await main_loop(args)

    transport.close()


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--ip", default="192.168.0.101", help="The ip to listen on")
    PARSER.add_argument("--port", type=int, default=9999, help="The port to listen on")
    PARSER.add_argument(
        "--on_offset", type=int, default=-120, help="minutes before sunset"
    )
    PARSER.add_argument("--end_time", type=str, default="11:00", help="end time")
    PARSER.add_argument(
        "--animate", type=int, default=30, help="seconds between animations"
    )
    PARSER.add_argument(
        "--animate_intervals",
        type=int,
        nargs="+",
        help="list of seconds between intervals",
    )
    PARSER.add_argument(
        "--enable_sun", type=int, default=1, help="enable use of solar timing"
    )
    ARGS = PARSER.parse_args()

    assert (
        True
        if not ARGS.animate_intervals
        else len(ARGS.animate_intervals) == len(ANIMATION_ORDER)
    )

    ERRMSG = YRefParam()
    if YAPI.RegisterHub("usb", ERRMSG) != YAPI.SUCCESS:
        LOGGER.error(f"YAPI init error {ERRMSG.value}")
    else:
        WATCHDOG = YWatchdog.FirstWatchdog()
        if WATCHDOG:
            WATCHDOG.resetWatchdog()
        else:
            LOGGER.error("No watchdog connected")

    DISPATCHER = Dispatcher()
    DISPATCHER.map("/letter/*", handle_letter)
    DISPATCHER.map("/word/*", handle_word)
    DISPATCHER.map("/full", handle_full)
    DISPATCHER.map("/animation/*", handle_animation)
    DISPATCHER.map("/parameter/*", handle_parameter)

    if RPI:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12, GPIO.OUT)
        signal(0.25, 2)

    handle_full("", None)

    asyncio.run(init_main(ARGS, DISPATCHER))
