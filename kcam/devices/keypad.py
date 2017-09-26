import evdev
import logging
import threading
import time

from collections import defaultdict

from kcam import observer

LOG = logging.getLogger(__name__)

keymap = {
    'KEY_0': '0',
    'KEY_1': '1',
    'KEY_2': '2',
    'KEY_3': '3',
    'KEY_4': '4',
    'KEY_5': '5',
    'KEY_6': '6',
    'KEY_7': '7',
    'KEY_8': '8',
    'KEY_9': '9',
    'KEY_KP0': '0',
    'KEY_KP1': '1',
    'KEY_KP2': '2',
    'KEY_KP3': '3',
    'KEY_KP4': '4',
    'KEY_KP5': '5',
    'KEY_KP6': '6',
    'KEY_KP7': '7',
    'KEY_KP8': '8',
    'KEY_KP9': '9',
}


def is_keypad(device):
    return (evdev.ecodes.KEY_KP1
            in device.capabilities()[evdev.ecodes.EV_KEY])


class Keypad(observer.Observable, threading.Thread):

    default_timeout = 10
    default_device = '/dev/input/event0'
    default_grab = True

    def __init__(self,
                 device=None,
                 device_name=None,
                 grab=None,
                 timeout=None,
                 **kwargs):

        super(Keypad, self).__init__(daemon=True, **kwargs)

        if device is None and device_name is None:
            device = self.default_device

        self.acc = []
        self.timeout = timeout if timeout else self.default_timeout
        self.keys = defaultdict(observer.Observable)

        if device:
            self.device = evdev.InputDevice(device)
        else:
            self.device = self.lookup_device(device_name)

        LOG.info('using input device %s', self.device)

        grab = grab if grab is not None else self.default_grab
        if grab:
            self.device.grab()

    def lookup_device(self, name):
        LOG.debug('looking for input device "%s"', name)
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        for dev in devices:
            if dev.name == name and is_keypad(dev):
                return dev

        raise KeyError('no device named %s' % name)

    def run(self):
        LOG.debug('starting keypad thread')
        last_event = time.time()

        for event in self.device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                this_event = time.time()
                key = evdev.categorize(event)

                LOG.debug('keycode event for %s %s',
                          key.keycode,
                          'down' if key.keystate else 'up')

                # only handle key-up events
                if key.keystate:
                    continue

                if this_event - last_event > self.timeout:
                    LOG.debug('keypad timeout; clearing buffer')
                    self.acc = []

                if key.keycode in self.keys:
                    self.keys[key.keycode].notify_observers()
                elif key.keycode in keymap:
                    self.acc.append(keymap[key.keycode])
                elif key.keycode in ['KEY_ENTER', 'KEY_KPENTER']:
                    self.process_input()

                last_event = this_event

        LOG.debug('stopping keypad thread')

    def process_input(self):
        data = ''.join(self.acc)
        self.acc = []

        LOG.debug('sending keypad input: %s', data)
        self.notify_observers(data)
