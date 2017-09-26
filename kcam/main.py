import argparse
import configparser
import logging
import os
import signal

from pathlib import Path
from RPi import GPIO

from kcam.camera import Camera
from kcam.defaults import DEFAULTS
from kcam.devices.blink import Blink
from kcam.devices.buzzer import Buzzer
from kcam.devices.keypad import Keypad
from kcam.devices.led import LED
from kcam.metrics import MetricConnection
from kcam.sensors.activity import ActivitySensor
from kcam.sensors.gpio import GPIOSensor
from kcam.taskmanager import TaskManager
from kcam.tasks import (EncodeVideo,
                        GenerateThumbnails,
                        UpdateEventHTML,
                        UpdateEventListHTML)
from kcam.tunes import TUNE_ARMED, TUNE_DISARMED, TUNE_ERROR
from kcam.util import date_from_path

LOG = logging.getLogger(__name__)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class KCam(object):
    required_sections = [
        'metrics',
        'camera',
        'pins',
        'keypad',
        'buzzer',
        'sensor:motion',
        'sensor:door',
        'sensor:activity',
    ]

    def __init__(self, config):
        self.config = config
        self.threads = []
        self.armed = False

        self.init_config()
        self.create_taskmanager()
        self.create_leds()
        self.create_buttons()
        self.create_buzzer()
        self.create_metrics()
        self.create_sensors()
        self.create_camera()
        self.create_keypad()

    def init_config(self):
        for section in self.required_sections:
            if section not in self.config:
                self.config.add_section(section)

    def create_buzzer(self):
        if self.config['buzzer'].getboolean('buzzer_enable'):
            self.buzzer = Buzzer(
                self.config.getint('pins', 'buzzer_pin'),
            )
        else:
            self.buzzer = Buzzer(None)

    def create_taskmanager(self):
        self.postprocess = TaskManager()
        self.threads.append(self.postprocess)
        self.postprocess.add_task((EncodeVideo(), GenerateThumbnails()))
        self.postprocess.add_task((UpdateEventHTML(), UpdateEventListHTML()))

    def create_buttons(self):
        self.arm_btn = GPIOSensor(
            self.config.getint('pins', 'arm_btn_pin'),
            pull_down=True,
            bouncetime=200)
        self.threads.append(self.arm_btn)
        self.arm_btn.add_observer(self, self.handle_arm_button)

    def create_leds(self):
        self.pwr_led = LED(self.config.getint('pins', 'pwr_led_pin'))
        self.pwr_led_blink = Blink()
        self.pwr_led_blink.add_observer(self.pwr_led, self.pwr_led.set)
        self.threads.append(self.pwr_led_blink)

        self.act_led = LED(self.config.getint('pins', 'act_led_pin'))
        self.det_led = LED(self.config.getint('pins', 'det_led_pin'))
        self.arm_led = LED(self.config.getint('pins', 'arm_led_pin'))

    def create_metrics(self):
        self.metrics = MetricConnection(
            host=self.config['metrics'].get('host'),
            port=self.config['metrics'].get('port'),
            database=self.config['metrics'].get('database'),
        )

    def create_keypad(self):
        self.keypad = Keypad(
            device_name=self.config['keypad'].get('keypad_device_name'),
            device=self.config['keypad'].get('keypad_device'),
            grab=self.config['keypad'].getboolean('keypad_grab'),
        )
        self.threads.append(self.keypad)
        self.keypad.add_observer(self, self.handle_passcode_attempt)
        arm_key = self.config['keypad'].get('keypad_arm_key')
        if arm_key:
            self.keypad.keys[arm_key].add_observer(self, self.handle_arm_key)
        self.passcode = self.config['DEFAULT'].get('passcode')

    def create_sensors(self):
        self.motion_sensor = GPIOSensor(
            self.config.getint('sensor:motion', 'motion_pin'),
            pull_up=True)
        self.motion_sensor.add_observer(self.det_led, self.det_led.set)
        self.motion_sensor.add_observer(self.metrics.create_observer('motion'))
        self.threads.append(self.motion_sensor)

        self.door_sensor = GPIOSensor(
            self.config.getint('sensor:door', 'door_pin'),
            pull_up=True)
        self.door_sensor.add_observer(self.metrics.create_observer('door'))
        self.threads.append(self.door_sensor)

        self.activity_sensor = ActivitySensor(
            interval=self.config['sensor:activity'].getint('activity_interval'),
            extend=self.config['sensor:activity'].getint('activity_extend'),
            limit=self.config['sensor:activity'].getint('activity_limit'),
            cooldown=self.config['sensor:activity'].getint('activity_cooldown'),
        )
        self.activity_sensor.add_observer(self.act_led, self.act_led.set)
        self.activity_sensor.add_observer(self.metrics.create_observer('activity'))
        self.activity_sensor.stopwatch.add_observer(
            self.metrics.create_observer('activity_duration'))

    def create_camera(self):
        self.camera = Camera(
            res_x=self.config['camera'].getint('camera_res_x'),
            res_y=self.config['camera'].getint('camera_res_y'),
            lead_time=self.config['camera'].getint('camera_lead_time'),
            datadir=self.config.get('DEFAULT', 'datadir'),
            eventdir=self.config['camera'].get('camera_eventdir'),
            imagename=self.config['camera'].get('camera_imagename'),
            videoname=self.config['camera'].get('camera_videoname'),
            interval=self.config['camera'].getint('camera_interval'),
            flip=self.config['camera'].getboolean('camera_flip'),
        )
        self.threads.append(self.camera)
        self.camera.add_observer(self.postprocess)
        self.activity_sensor.add_observer(self.camera)

    def arm(self):
        self.armed = True
        self.arm_led.on()
        self.motion_sensor.add_observer(self.activity_sensor)
        self.buzzer.play(TUNE_ARMED)
        LOG.warning('armed')

    def disarm(self):
        self.armed = False
        self.arm_led.off()
        self.motion_sensor.delete_observer(self.activity_sensor)
        self.buzzer.play(TUNE_DISARMED)
        LOG.warning('disarmed')

    def handle_passcode_attempt(self, passcode):
        LOG.debug('handling passcode attempt want "%s" got "%s"',
                  self.passcode, passcode)
        if passcode == self.passcode:
            LOG.info('received correct passcode')
            self.toggle_armed()
        else:
            self.buzzer.play(TUNE_ERROR)
            LOG.error('received incorrect passcode')

    def toggle_armed(self):
        if self.armed:
            self.disarm()
        else:
            self.arm()

    def handle_arm_button(self, pressed):
        LOG.debug('arm button pressed when %s',
                  'armed' if self.armed else 'not armed')
        if pressed and not self.armed:
            self.arm()

    def handle_arm_key(self, key):
        LOG.debug('arm key %s pressed', key)
        if not self.armed:
            self.arm()

    def run(self):
        LOG.info('kcam starting up')
        for thread in self.threads:
            thread.start()

        LOG.info('kcam startup complete')
        try:
            signal.pause()
        except KeyboardInterrupt:
            pass

        LOG.info('kcam shutting down')
        for thread in self.threads:
            try:
                thread.stop()
            except AttributeError:
                pass

        LOG.info('waiting for threads to complete')
        for thread in self.threads:
            try:
                if not thread.daemon:
                    thread.join()
            except AttributeError:
                pass

        LOG.info('kcam shutdown complete')


def KeyValueArgument(value):
    try:
        k, v = value.split('=', 1)
        return k, v
    except ValueError:
        raise argparse.ArgumentError('values must of the form <key>=<value>')


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument('--config', '-f',
                   default='kcam.conf')
    p.add_argument('--arm',
                   action='store_true')
    p.add_argument('--datadir', '-D')

    g = p.add_argument_group('Logging options')
    g.add_argument('--verbose', '-v',
                   action='store_const',
                   const='INFO',
                   dest='loglevel')
    g.add_argument('--debug', '-d',
                   action='store_const',
                   const='DEBUG',
                   dest='loglevel')
    g.add_argument('--set-logger', '-l',
                   action='append',
                   default=[],
                   type=KeyValueArgument)

    p.set_defaults(loglevel='WARNING')

    return p.parse_args()


def process_cli():
    args = parse_args()
    logging.basicConfig(level=args.loglevel)
    config = configparser.ConfigParser(defaults=DEFAULTS)
    config.read(args.config)

    if args.datadir:
        config['DEFAULT']['datadir'] = args.datadir

    if args.set_logger:
        for name, level in args.set_logger:
            logger = logging.getLogger(name)
            logger.setLevel(level.upper())

    return args, config


def update_html():
    args, config = process_cli()
    update_event = UpdateEventHTML()
    update_eventlist = UpdateEventListHTML()
    datadir = config.get('DEFAULT', 'datadir')

    events = []
    for root, dirs, files in os.walk(datadir):
        root = Path(root)
        relpath = root.relative_to(datadir)
        if len(str(relpath).split('/')) != 4:
            continue

        event = date_from_path(relpath)

        update_event({
            'datadir': datadir,
            'path': root,
            'event': event,
        })

    update_eventlist({
        'datadir': datadir,
    })


def main():
    args, config = process_cli()
    app = KCam(config)
    if args.arm:
        app.arm()

    app.run()


if __name__ == '__main__':
    main()
