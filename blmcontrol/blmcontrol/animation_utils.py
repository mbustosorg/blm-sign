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
import logging
import os
import random
import time

from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
from urllib.request import urlopen
from twilio.rest import Client

try:
    import smbus

    SMBUS = True
except ImportError:
    SMBUS = False

LOGGER = logging.getLogger("blm-sign")

DEVICE1 = 0x26
DEVICE2 = 0x27
IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

if SMBUS:
    try:
        BUS = smbus.SMBus(0)
    except:
        BUS = smbus.SMBus(1)
    try:
        BUS.write_byte_data(DEVICE1, IODIRA, 0x00)
        BUS.write_byte_data(DEVICE1, IODIRB, 0x00)
        BUS.write_byte_data(DEVICE1, OLATA, 0)
        BUS.write_byte_data(DEVICE1, OLATB, 0)
    except:
        LOGGER.info("Unable to initialize DEVICE1 I2C")
    try:
        BUS.write_byte_data(DEVICE2, IODIRA, 0x00)
        BUS.write_byte_data(DEVICE2, IODIRB, 0x00)
        BUS.write_byte_data(DEVICE2, OLATA, 0)
        BUS.write_byte_data(DEVICE2, OLATB, 0)
    except:
        pass

try:
    from RPi import GPIO

    RPI = True
except ImportError:
    RPI = False


FAST = 0.05
MEDIUM = 1.5
SLOW = 3.0
TIMES = 12
MESSAGE_LENGTH = 0
MAX_PWM = 3900

DISPLAY_MAPS = {}
SIGNAL = False

pwm = None
last_cell_check = datetime.datetime.now()


def check_cell_connectivity(retest: bool = False):
    """Ensure that we can reach out with cell service"""
    global last_cell_check

    if ((datetime.datetime.now() - last_cell_check).seconds < 600) and not retest:
        return

    last_cell_check = datetime.datetime.now()
    try:
        urlopen('http://www.google.com', timeout=60)
        LOGGER.info(f"Cell connectivity confirmed")
        return
    except Exception as e:
        LOGGER.error(f"Exception during connectivity check: {str(e)}")
        pass

    if retest:
        LOGGER.warning(f"Connectivity not restored, rebooting...")
        os.system("sudo reboot")

    LOGGER.warning(f"No internet connectivity")
    try:
        usb_interface = ni.ifaddresses('usb0')
        if AF_INET in usb_interface:
            addr = usb_interface[AF_INET][0]['addr']
            if addr:
                LOGGER.warning(f"Attempting dhclient")
                os.system("sudo dhclient -v usb0")
            else:
                LOGGER.warning(f"IP missing on usb0, rebooting...")
                os.system("sudo reboot")
        else:
            LOGGER.warning(f"IP missing on usb0, rebooting...")
            os.system("sudo reboot")
    except Exception as e:
        LOGGER.error(f"Exception during 'No internet connectivity' {str(e)}")
        raise e


def animate_interval(index: int, args) -> int:
    """Next animation interval"""
    if args.animate_intervals:
        return args.animate_intervals[index]
    return args.animate


def signal(length, count):
    """ Signal status on buzzer """
    if RPI and SIGNAL:
        for _ in range(0, count):
            GPIO.output(12, True)
            time.sleep(length)
            GPIO.output(12, False)
            time.sleep(length)


def set_signal(args):
    """Setup buzzer"""
    global SIGNAL

    SIGNAL = args.signal

    if RPI and SIGNAL:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12, GPIO.OUT)
        signal(0.15, 2)


def set_pwm(pwm_driver):
    """Set local pwm driver"""
    global pwm
    pwm = pwm_driver


def gamma(original, correction=0.4):
    """ Gamma correction for LED strips """
    return int(((original / 4096.0) ** (1 / correction)) * 4096)


def set_timing(name: str, value):
    """ Set parameter values """
    global FAST, MEDIUM, SLOW, TIMES
    LOGGER.info(f"{name}: {value}")
    if name == "fast":
        FAST = value
    if name == "medium:":
        MEDIUM = value
    if name == "slow":
        SLOW = value
    if name == "times":
        TIMES = int(value)


def push_data_pwm(value, hands=0xFF):
    """ Push data to I2C devices """
    for i in range(8):
        if value & 1 << i:
            pwm.set_pwm(i, 0, gamma(MAX_PWM))
        else:
            pwm.set_pwm(i, 0, 0)


def push_data(value, hands=0xFF):
    """ Push data to I2C devices """
    if pwm:
        push_data_pwm(value, hands)
        return
    if SMBUS:
        try:
            BUS.write_byte_data(DEVICE1, OLATA, value & 0xFF)
            BUS.write_byte_data(DEVICE1, OLATB, (value & 0xFF00) >> 8)
            BUS.write_byte_data(DEVICE2, OLATA, hands)
            BUS.write_byte_data(DEVICE2, OLATB, 0xFF)
        except:
            BUS.write_byte_data(DEVICE2, OLATB, value & 0xFF)
    #print(f"{int('{:016b}'.format(value)[::-1], 2):#018b}", end="\r")


def clear():
    """ Clear the display """
    push_data(DISPLAY_MAPS["FULL"])


def window():
    """ Slide window across """
    for _ in range(0, int(TIMES)):
        bit = 0
        for j in range(0, MESSAGE_LENGTH):
            bit = bit | 0x1 << j
            push_data(bit)
            time.sleep(FAST)
        for j in range(0, MESSAGE_LENGTH):
            bit = 0xFFFF << (j + 1)
            push_data(bit)
            time.sleep(FAST)
        push_data(0)


def scroll():
    """ Left to right one letter at time """
    for _ in range(0, int(TIMES)):
        for j in range(0, MESSAGE_LENGTH):
            bit = 0x1 << j
            push_data(bit)
            time.sleep(FAST)
    clear()


def random_letters():
    """ Random letter """
    samples = random.sample(range(0, MESSAGE_LENGTH), MESSAGE_LENGTH)
    for _ in range(0, int(TIMES)):
        for j in samples:
            bit = 0x1 << j
            push_data(bit)
            time.sleep(FAST)
    clear()


def flickering():
    """ Flicker a random couple letters """
    letter = 0x1 << int(random.random() * 16)
    if random.randint(1, 2) == 1:
        primary = 0xFFFF & ~letter
        secondary = 0xFFFF
    else:
        primary = 0xFFFF
        secondary = 0xFFFF & ~letter
    for i in range(0, 45):
        time_sample = random.random()
        push_data(primary)
        time.sleep(time_sample)
        push_data(secondary)
        time.sleep(0.1)
    clear()


def startup(shutdown: bool = False):
    """ Simulate starting up a neon light """
    start_time = [max(random.random() * 1.0, 0.1) for _ in range(0, 16)]
    periods = [(x, x * 2, x * 3, x * 4) for x in start_time]
    start = datetime.datetime.now()
    display = 0
    while display != 0xFFFF:
        delta = datetime.datetime.now() - start
        clock = float(delta.seconds) + delta.microseconds / 1000000.0
        for i, x in enumerate(periods):
            if clock > x[3] + 0.2:
                display = display | 0x1 << i
            elif clock > x[3] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[3]:
                display = display | 0x1 << i
            elif clock > x[2] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[2]:
                display = display | 0x1 << i
            elif clock > x[1] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[1]:
                display = display | 0x1 << i
            elif clock > x[0] + 0.1:
                display = display & ~(0x1 << i)
            elif clock > x[0]:
                display = display | 0x1 << i
        push_data(display if not shutdown else 0xFFFF - display)
    time.sleep(3)
    clear()


def random_letters():
    """ Random letter """
    samples = random.sample(range(0, MESSAGE_LENGTH), MESSAGE_LENGTH)
    for i in range(0, int(TIMES)):
        for j in samples:
            bit = 0x1 << j
            push_data(bit)
            time.sleep(FAST)
    clear()


def broadcast_message(message: str):
    """Broadcast SMS message"""
    try:
        check_cell_connectivity()
        client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
        message = client.messages.create(body=message, from_="+14302026708", to="+15103261619")
        LOGGER.info("SMS message sent: " + message.sid)
    except Exception as e:
        LOGGER.error(str(e))
        pass


def startup_shutdown():
    """Flash up then down"""
    startup(False)
    startup(True)
    push_data(0)
    time.sleep(0.5)
    clear()
    time.sleep(1)
    push_data(0)
    time.sleep(0.5)
    clear()
    time.sleep(1)
    push_data(0)
    time.sleep(0.5)
    clear()
