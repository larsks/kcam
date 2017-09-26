import logging
import time

from kcam.common import Application
from kcam.devices.buzzer import Buzzer

LOG = logging.getLogger(__name__)


class TestBuzzerApplication(Application):
    def required_config_sections(self):
        sections = super(TestBuzzerApplication, self).required_config_sections()
        return sections + ['buzzer']

    def create_overrides(self):
        overrides = super(TestBuzzerApplication, self).create_overrides()

        overrides.update({
            'pwm': ('buzzer', 'buzzer_pwm_path'),
            'enable': ('buzzer', 'buzzer_enable'),
        })

        return overrides

    def create_parser(self):
        p = super(TestBuzzerApplication, self).create_parser()

        g = p.add_argument_group('Buzzer options')
        g.add_argument('--pwm')
        g.add_argument('--disable',
                       action='store_const',
                       const='false',
                       dest='enable')
        g.add_argument('--iterations',
                       default=1,
                       type=int)
        g.add_argument('--delay',
                       default=0,
                       type=float)

        p.add_argument('notes', nargs='*')

        return p

    def main(self):
        self.buzzer = Buzzer(
            pwm=self.config.get('buzzer', 'buzzer_pwm_path'),
            enable=self.config.getboolean('buzzer', 'buzzer_enable'),
        )

        for i in range(self.args.iterations):
            noteiter = iter(self.args.notes)
            notes = zip(noteiter, noteiter)
            self.buzzer.play(notes)
            time.sleep(self.args.delay)

    def update(self, arg):
        print('tune finished!')
        self.done_playing.set()

app = TestBuzzerApplication()


def main():
    app.run()

if __name__ == '__main__':
    main()
