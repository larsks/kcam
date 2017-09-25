import logging
import threading

from kcam.common import Application
from kcam.devices.buzzer import Buzzer

LOG = logging.getLogger(__name__)


class TestBuzzerApplication(Application):
    def required_config_sections(self):
        sections = super(TestBuzzerApplication, self).required_config_sections()
        return sections + ['pins']

    def create_overrides(self):
        overrides = super(TestBuzzerApplication, self).create_overrides()

        overrides.update({
            'pin': ('pins', 'buzzer_pin'),
        })

        return overrides

    def create_parser(self):
        p = super(TestBuzzerApplication, self).create_parser()

        g = p.add_argument_group('Buzzer options')
        g.add_argument('--pin')

        p.add_argument('notes', nargs='*')

        return p

    def main(self):
        self.buzzer = Buzzer(
            pin=self.config.getint('pins', 'buzzer_pin'),
        )
        self.buzzer.add_observer(self)
        self.done_playing = threading.Event()

        self.buzzer.start()

        noteiter = iter(self.args.notes)
        notes = zip(noteiter, noteiter)
        self.buzzer.play(notes)
        self.done_playing.wait()

    def update(self, arg):
        print('tune finished!')
        self.done_playing.set()

app = TestBuzzerApplication()


def main():
    app.run()

if __name__ == '__main__':
    main()
