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

    def play_tone(self, freq, duration):
        '''Play a single tone using pwm'''
        freq, duration = float(freq), float(duration)
        LOG.debug('play %f for %f seconds', freq, duration)

        if freq == 0:
            time.sleep(duration)
            return

        self.set_frequency(freq)

        try:
            self.enable_output()
            time.sleep(duration)
        finally:
            self.disable_output()

    def enable_output(self):
        '''Enable pwm output'''
        if not self.enable:
            return

        with (self.pwm / 'enable').open('wb') as fd:
            fd.write(b'1\n')

    def disable_output(self):
        '''Disable pwm output'''
        with (self.pwm / 'enable').open('wb') as fd:
            fd.write(b'0\n')

    def set_period(self, period, duty_cycle=0.5):
        '''Set pwm period (specified in ns)'''

        period_bytes = bytes('%s' % int(period), 'ascii')

        self.set_duty_cycle(0, 0)
        with (self.pwm / 'period').open('wb') as fd:
            fd.write(period_bytes)
        self.set_duty_cycle(period, duty_cycle)

    def set_duty_cycle(self, period, duty_cycle=0.5):
        if duty_cycle > 1 or duty_cycle < 0:
            raise ValueError('0 <= duty_cycle <= 1')

        duty_cycle = duty_cycle * period
        duty_cycle_bytes = bytes('%s' % int(duty_cycle), 'ascii')
        with (self.pwm / 'duty_cycle').open('wb') as fd:
            fd.write(duty_cycle_bytes)

    def set_frequency(self, freq, **kwargs):
        '''Convert a frequency in Hz to a period in ns'''

        period = (1.0 / freq) * 1e+9
        self.set_period(period, **kwargs)

    def play(self, tune):
        LOG.debug('play tune %s', tune)
        for freq, duration in tune:
            self.play_tone(freq, duration)
