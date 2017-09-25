import logging
import queue
import threading
import time

from RPi import GPIO

from kcam import observer

LOG = logging.getLogger(__name__)


class Buzzer(observer.Observable, threading.Thread):

    def __init__(self, pin, init_val=0, **kwargs):
        super(Buzzer, self).__init__(daemon=True, **kwargs)

        self.pin = int(pin)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, init_val)
        self.q = queue.Queue()

    def play(self, tune):
        self.q.put(tune)

    def run(self):
        LOG.debug('started buzzer thread')
        while True:
            tune = self.q.get()
            LOG.debug('received tune: %s', tune)
            self.play_tune(tune)

    def play_tone(self, pitch, duration):
        pitch, duration = float(pitch), float(duration)

        if pitch == 0:
            time.sleep(duration)
            return

        period = 1.0 / pitch
        delay = period / 2
        cycles = int(duration * pitch)

        for i in range(cycles):
            GPIO.output(self.pin, True)
            time.sleep(delay)
            GPIO.output(self.pin, False)
            time.sleep(delay)

    def play_tune(self, tune):
        for pitch, duration in tune:
            self.play_tone(pitch, duration)

        self.notify_observers(None)
