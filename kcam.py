from RPi import GPIO
from signal import pause

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

    def __init__(self, pin=None, handler=None):
        self.pin = int(pin)
        self.handler = handler
        self.setup_pin()

    def setup_pin(self):
        GPIO.setup(self.pin, GPIO.IN)

    def enable(self):
        GPIO.add_event_detect(self.pin, GPIO.BOTH,
                              self.handler(self))

    def disable(self):
        GPIO.remove_event_detect(self.pin)

    @property
    def value(self):
        return GPIO.input(self.pin)


class Button:

    def __init__(self, pin, on_press=None, on_release=None):
        self.pin = pin
        self.setup_pin()
        self.on_press = on_press
        self.on_release = on_release

    def setup_pin(self):
        GPIO.setup(self.pin, GPIO.IN)

    def enable(self):
        GPIO.add_event_detect(self.pin, GPIO.BOTH,
                              self.handler(self))

    def disable(self):
        GPIO.remove_event_detect(self.pin)

    @property
    def value(self):
        return GPIO.input(self.pin)

    def handler(self, pin):
        if self.value and self.on_press:
            self.on_press(self)
        elif self.on_release:
            self.on_release(self)


class KCam:

    def __init__(self,
                 pir_pin=None,
                 pwr_led_pin=None,
                 arm_led_pin=None,
                 det_led_pin=None,
                 act_led_pin=None,
                 arm_btn_pin=None):

        self.pir_pin = pir_pin
        self.pwr_led = LED(pwr_led_pin)
        self.arm_led = LED(arm_led_pin)
        self.act_led = LED(act_led_pin)
        self.det_led = LED(det_led_pin)
        self.motion = MotionSensor(pir_pin, handler=self.on_motion)
        self.arm_btn = Button(arm_btn_pin,
                              on_press=self.on_arm_button)

        self.armed = False

    def arm(self):
        self.arm_led.on()
        self.motion.enable()
        self.armed = True

    def disarm(self):
        self.motion.disable()
        self.arm_led.off()
        self.armed = False

    def on_arm_button(self):
        if self.armed:
            self.disarm()
        else:
            self.arm()

    def setup_gpio(self):
        GPIO.setup(self.pir_pin, GPIO.IN)

    def setup_events(self):
        GPIO.add_event_callback(self.pir_pin, self.on_motion)

    def on_motion(self, pin):
        active = pin.value
        if active:
            self.det_led.on()
        else:
            self.det_led.off()


def main():
    cam = KCam(pir_pin=23, det_led_pin=24, act_led_pin=25,
               pwr_led_pin=17, arm_led_pin=27, arm_btn_pin=22)
    cam.setup_events()
    pause()


if __name__ == '__main__':
    main()
