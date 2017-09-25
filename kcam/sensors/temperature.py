import Adafruit_DHT
import logging
import threading

from kcam import observer

LOG = logging.getLogger(__name__)


devices = {
    'DHT22': Adafruit_DHT.DHT22,
    'DHT11': Adafruit_DHT.DHT11,
}


class TemperatureSensor(threading.Thread):
    default_interval = 60
    default_devicetype = Adafruit_DHT.DHT22

    def __init__(self, pin,
                 devicetype=None,
                 interval=None,
                 **kwargs):
        super(TemperatureSensor, self).__init__(**kwargs)
        self.pin = pin
        self.interval = interval if interval else self.default_interval
        self.devicetype = (devices[devicetype] if devicetype
                           else self.default_devicetype)
        self.evt_stop = threading.Event()

        self.temperature = observer.Value()
        self.humidity = observer.Value()
        self.mutex = threading.RLock()

    def __str__(self):
        return '<TemperatureSensor pin:%d interval:%d>' % (
            self.pin, self.interval)

    def stop(self):
        self.evt_stop.set()

    def run(self):
        LOG.info('starting temperature sensor %s', self)

        while True:
            humidity, temperature = Adafruit_DHT.read_retry(
                self.devicetype, self.pin)
            if humidity is not None and temperature is not None:
                LOG.info('got humidity = %f, temp = %f',
                         humidity, temperature)
                with self.mutex:
                    self.temperature.set(temperature)
                    self.humidity.set(humidity)

            else:
                LOG.error('failed to read temperature sensor')

            if self.evt_stop.wait(self.interval):
                break

        LOG.info('stopping temperature sensor on pin %d', self.pin)

    @property
    def value(self):
        with self.mutex:
            return dict(temperature=self.temperature.value,
                        humidity=self.humidity.value)
