import Adafruit_DHT
import logging
import threading
from collections import namedtuple

from . import observer

LOG = logging.getLogger(__name__)


sensors = {
    'DHT22': Adafruit_DHT.DHT22,
    'DHT11': Adafruit_DHT.DHT11,
}


TemperatureReading = namedtuple('TemperatureReading',
                                ['humidity', 'temperature'])


class TemperatureSensor(observer.Observable, threading.Thread):
    def __init__(self, pin, sensor='DHT22', read_interval=10, **kwargs):
        super(TemperatureSensor, self).__init__(**kwargs)
        self.read_interval = read_interval
        self.pin = pin
        self.sensor = sensors[sensor]
        self._value = (None, None)
        self.evt_quit = threading.Event()

    def quit(self):
        self.evt_quit.set()

    def run(self):
        LOG.info('starting temperature sensor on pin %d', self.pin)
        self.evt_quit.clear()

        while True:
            humidity, temperature = Adafruit_DHT.read_retry(
                self.sensor, self.pin)
            if humidity is not None and temperature is not None:
                LOG.debug('got humidity = %f, temp = %f',
                          humidity, temperature)
                with self.mutex:
                    self._value = TemperatureReading(humidity, temperature)
                    self.notify_observers(self._value)
            else:
                LOG.error('failed to read temperature sensor')

            if self.evt_quit.wait(self.read_interval):
                break

        LOG.info('stopping temperature sensor on pin %d', self.pin)

    def value(self):
        with self.mutex:
            return self._value
