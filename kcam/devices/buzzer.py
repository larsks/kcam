import logging
import time

from RPi import GPIO

LOG = logging.getLogger(__name__)


class Buzzer(object):

    def __init__(self, pin, init_val=0, **kwargs):
        super(Buzzer, self).__init__(**kwargs)

        if pin is not None:
            self.pin = int(pin)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, init_val)
        else:
            self.pin = None

    def play_tone(self, pitch, duration):
        pitch, duration = float(pitch), float(duration)

        if pitch == 0:
            time.sleep(duration)
            return

        period = 1.0 / pitch
        delay = period / 2
        cycles = int(duration * pitch)

        if self.pin is not None:
            p = GPIO.PWM(self.pin, pitch)
            p.start(0.5)
            time.sleep(duration)
            p.stop()

    def play(self, tune):
        for pitch, duration in tune:
            self.play_tone(pitch, duration)
