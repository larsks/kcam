import logging

from RPi import GPIO

from kcam import observer

LOG = logging.getLogger(__name__)
GPIO.setmode(GPIO.BCM)


class GPIOSensor(observer.Observable):
    def __init__(self, pin, edge=GPIO.BOTH, bouncetime=None, **kwargs):
        super(GPIOSensor, self).__init__(**kwargs)
        self.pin = pin
        self.edge = edge
        self.value = None
        self.bouncetime = bouncetime

        LOG.info('configuring gpio sensor on pin %d', pin)
        GPIO.setup(pin, GPIO.IN)

    def start(self):
        kwargs = {}
        if self.bouncetime is not None:
            kwargs['bouncetime'] = self.bouncetime

        LOG.info('starting gpio sensor on pin %d', self.pin)
        GPIO.add_event_detect(self.pin,
                              edge=self.edge,
                              callback=self.handle_event,
                              **kwargs)

    def stop(self):
        LOG.info('stopping gpio sensor on pin %d', self.pin)
        GPIO.remove_event_detect(self.pin)

    def handle_event(self, pin):
        if pin != self.pin:
            raise ValueError('received event for unknown pin %d '
                             '(expected %d)' % (pin, self.pin))

        self.read()
        LOG.debug('gpio event on pin %d, value = %d', self.pin, self.value)
        self.notify_observers(self.value)

    def read(self):
        self.value = GPIO.input(self.pin)
        return self.value
