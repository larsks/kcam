import logging
import threading

from RPi import GPIO
from signal import pause

from . import timer

LOG = logging.getLogger('kcam')
GPIO.setmode(GPIO.BCM)


class LED:

    def __init__(self, pin=None):
        self.pin = int(pin)
        self.setup_pin()

    def setup_pin(self):
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, 0)

    def on(self):
        GPIO.output(self.pin, 1)

    def off(self):
        GPIO.output(self.pin, 0)


class MotionSensor:

    def __init__(self, pin=None, on_motion=None, on_no_motion=None):
        self.pin = int(pin)
        self.on_motion = on_motion
        self.on_no_motion = on_no_motion

        self.setup_pin()

    def setup_pin(self):
        GPIO.setup(self.pin, GPIO.IN)

    def enable(self):
        LOG.info('enabling motion sensors on pin %d', self.pin)
        GPIO.add_event_detect(self.pin, GPIO.BOTH,
                              callback=self.handler)

    def disable(self):
        GPIO.remove_event_detect(self.pin)

    @property
    def value(self):
        return GPIO.input(self.pin)

    def handler(self, pin):
        LOG.debug('motion event on pin %d', pin)
        if self.on_motion and self.value:
            self.on_motion(self)
        elif self.on_no_motion:
            self.on_no_motion(self)


class Button:

    def __init__(self, pin, on_press=None, bouncetime=200):
        self.pin = pin
        self.on_press = on_press
        self.bouncetime = bouncetime

        self.setup_pin()

    def setup_pin(self):
        GPIO.setup(self.pin, GPIO.IN)

    def enable(self):
        LOG.info('enabling button on pin %d', self.pin)
        GPIO.add_event_detect(self.pin, GPIO.RISING,
                              callback=self.handler,
                              bouncetime=self.bouncetime)

    def disable(self):
        GPIO.remove_event_detect(self.pin)

    @property
    def value(self):
        return GPIO.input(self.pin)

    def handler(self, pin):
        LOG.debug('button event on pin %d', pin)
        if self.value and self.on_press:
            self.on_press(self)


class KCam:

    def __init__(self,
                 pir_pin=None,
                 pwr_led_pin=None,
                 arm_led_pin=None,
                 det_led_pin=None,
                 act_led_pin=None,
                 arm_btn_pin=None,
                 arm_delay=None,
                 cooldown_interval=None,
                 record_interval=10,
                 record_limit=300):

        self.pir_pin = pir_pin
        self.pwr_led = LED(pwr_led_pin)
        self.arm_led = LED(arm_led_pin)
        self.act_led = LED(act_led_pin)
        self.det_led = LED(det_led_pin)
        self.motion = MotionSensor(pir_pin,
                                   on_motion=self.on_motion,
                                   on_no_motion=self.on_no_motion)

        self.arm_btn = Button(arm_btn_pin,
                              on_press=self.on_arm_button)

        self.active = False
        self.arm_delay = arm_delay
        self.armed = False
        self.cooldown = False
        self.cooldown_interval = cooldown_interval
        self.record_interval = record_interval
        self.record_limit = record_limit

        self.disarm()

    def enable(self):
        self.arm_btn.enable()
        self.pwr_led.on()

    def disable(self):
        self.arm_btn.disable()
        self.pwr_led.off()

    def arm(self):
        LOG.info('arm')
        self.arm_led.on()
        self.motion.enable()
        self.armed = True

    def disarm(self):
        LOG.info('disarm')
        self.motion.disable()
        self.arm_led.off()
        self.armed = False

    def on_arm_button(self, pin):
        if self.armed:
            self.disarm()
        else:
            self.arm()

    def on_motion(self, pin):
        LOG.info('motion detected')
        self.det_led.on()

        if not self.cooldown:
            if not self.active:
                self.start_active()
            else:
                self.continue_active()
        else:
            LOG.info('ignoring motion during cooldown period')

    def on_no_motion(self, pin):
        LOG.info('motion not detected')
        self.det_led.off()

    def start_active(self):
        LOG.info('start activity')
        self.act_led.on()
        self.active = True
        self.timer = timer.DynamicTimer(
            interval=self.record_interval,
            function=self.stop_active,
            limit=self.record_limit)

    def continue_active(self):
        LOG.info('continue activity')
        self.timer.update(self.record_interval)

    def stop_active(self):
        LOG.info('stop activity')
        self.act_led.off()
        self.active = False
        self.start_cooldown()

    def start_cooldown(self):
        LOG.info('start cooldown period')
        self.cooldown = True
        self.timer = timer.DynamicTimer(
            interval=self.cooldown_interval,
            function=self.stop_cooldown)

    def stop_cooldown(self):
        LOG.info('end cooldown period')
        self.cooldown = False


def main():
    logging.basicConfig(level='DEBUG')
    cam = KCam(pir_pin=23, det_led_pin=24, act_led_pin=25,
               pwr_led_pin=17, arm_led_pin=27, arm_btn_pin=22)
    cam.enable()
    pause()


if __name__ == '__main__':
    main()
