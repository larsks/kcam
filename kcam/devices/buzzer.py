import logging
import time

from pathlib import Path

LOG = logging.getLogger(__name__)


class Buzzer(object):

    '''Drive a piezo buzzer using hardware PWM.

    The raspberry pi has one or two hardware PWM pins available. We can
    use this to drive a piezeo buzzer rather than relying on software
    pwm, which is lower quality and, in the case of RPi.GPIO, crashy.

    For details, see
    http://www.jumpnowtek.com/rpi/Using-the-Raspberry-Pi-Hardware-PWM-timers.html

    This implementation assumes that we are *not* running as root, so
    the pwm must be configured externally to this code.
    '''

    def __init__(self, pwm, enable=True, **kwargs):
        '''Configure a hardware PWM.

        `pwm` is a full path to a pwm device in sysfs.  E.g.,
        /sys/class/pwm/pwmchip0/pwm1.
        '''

        super(Buzzer, self).__init__(**kwargs)

        self.pwm = Path(pwm)
        self.enable = enable

        LOG.info('created buzzer on %s', self.pwm)

    def play_tone(self, pitch, duration):
        pitch, duration = float(pitch), float(duration)
        LOG.debug('play %f for %f seconds', pitch, duration)

        if pitch == 0:
            time.sleep(duration)
            return

        period = (1.0 / pitch) * 1e+9
        duty_cycle = period / 2

        period_bytes = bytes('%s' % int(period), 'ascii')
        duty_cycle_bytes = bytes('%s' % int(duty_cycle), 'ascii')

        with (self.pwm / 'period').open('wb') as fd:
            fd.write(period_bytes)

        with (self.pwm / 'duty_cycle').open('wb') as fd:
            fd.write(duty_cycle_bytes)

        try:
            enable = b'1\n' if self.enable else b'0\n'
            with (self.pwm / 'enable').open('wb') as fd:
                fd.write(enable)

            time.sleep(duration)
        finally:
            with (self.pwm / 'enable').open('wb') as fd:
                fd.write(b'0\n')

    def play(self, tune):
        LOG.debug('play tune %s', tune)
        for pitch, duration in tune:
            self.play_tone(pitch, duration)
