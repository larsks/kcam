import Adafruit_DHT
import logging
import threading

from kcam import observer

LOG = logging.getLogger(__name__)


sensors = {
    'DHT22': Adafruit_DHT.DHT22,
    'DHT11': Adafruit_DHT.DHT11,
}


class TemperatureSensor(observer.Observable, threading.Thread):
    def __init__(self, pin,
                 sensor='DHT22',
                 read_interval=10,
                 **kwargs):
        super(TemperatureSensor, self).__init__(**kwargs)
        self.read_interval = read_interval
        self.pin = pin
        self.sensor = sensors[sensor]
        self.evt_stop = threading.Event()

        self.temperature = None
        self.humidity = None

    def stop(self):
        self.evt_stop.set()

    def run(self):
        LOG.info('starting temperature sensor on pin %d', self.pin)
        self.evt_stop.clear()

        while True:
            humidity, temperature = Adafruit_DHT.read_retry(
                self.sensor, self.pin)
            if humidity is not None and temperature is not None:
                LOG.debug('got humidity = %f, temp = %f',
                          humidity, temperature)
                with self.mutex:
                    self.temperature = temperature
                    self.humidity = humidity

                self.notify_observers(self.value)

            else:
                LOG.error('failed to read temperature sensor')

            if self.evt_stop.wait(self.read_interval):
                break

        LOG.info('stopping temperature sensor on pin %d', self.pin)

    @property
    def value(self):
        with self.mutex:
            return dict(temperature=self.temperature,
                        humidity=self.humidity)
