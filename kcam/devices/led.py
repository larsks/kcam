import logging

from RPi import GPIO

LOG = logging.getLogger(__name__)


class LED(object):

    def __init__(self, pin, init_val=0):
        self.pin = int(pin)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, init_val)

    def on(self):
        self.set(1)

    def off(self):
        self.set(0)

    def set(self, val):
        val = int(val)
        if val < 0 or val > 1:
            raise ValueError('val must be either 0 or 1')
        LOG.debug('set led on pin %d to %d', self.pin, val)
        GPIO.output(self.pin, val)
