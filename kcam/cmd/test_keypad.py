import logging
import signal

from kcam.common import Application
from kcam.devices.keypad import Keypad

LOG = logging.getLogger(__name__)


class TestKeypadApplication(Application):
    def required_config_sections(self):
        sections = super(TestKeypadApplication, self).required_config_sections()
        return sections + ['keypad']

    def create_overrides(self):
        overrides = super(TestKeypadApplication, self).create_overrides()

        overrides.update({
            'device': ('keypad', 'keypad_device'),
            'device_name': ('keypad', 'keypad_device_name'),
            'arm_key': ('keypad', 'keypad_arm_key'),
        })

        return overrides

    def create_parser(self):
        p = super(TestKeypadApplication, self).create_parser()

        g = p.add_argument_group('Keypad options')
        g.add_argument('--device')
        g.add_argument('--device-name')
        g.add_argument('--arm-key')

        return p

    def main(self):
        self.keypad = Keypad(
            device=self.config['keypad'].get('keypad_device'),
            device_name=self.config['keypad'].get('keypad_device_name'),
        )

        arm_key = self.config['keypad'].get('keypad_arm_key')
        if arm_key:
            self.keypad.keys[arm_key].add_observer(self, self.handle_arm_key)

        self.keypad.start()

        try:
            signal.pause()
        except KeyboardInterrupt:
            pass

    def handle_arm_key(self, key):
        LOG.warning('arm key was pressed!')

    def handle_passcode(self, passcode):
        LOG.warning('received passcode: %s', passcode)

app = TestKeypadApplication()


def main():
    app.run()

if __name__ == '__main__':
    main()
