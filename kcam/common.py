import argparse
import configparser
import logging

from kcam.defaults import DEFAULTS


def KeyValueArgument(value):
    try:
        k, v = value.split('=', 1)
        return k, v
    except ValueError:
        raise argparse.ArgumentError('values must of the form <key>=<value>')


class Application(object):
    def __init__(self):
        self.parser = self.create_parser()
        self.config = self.create_config()
        self.overrides = self.create_overrides()

    def run(self, args=None):
        self.args = self.parse_args(args=args)

        self.configure_logging()
        self.parse_config()
        self.process_overrides()
        return self.main()

    def required_config_sections(self):
        return []

    def create_config(self):
        config = configparser.ConfigParser(
            defaults=DEFAULTS,
        )

        for section in self.required_config_sections():
            config.add_section(section)

        return config

    def parse_config(self):
        self.config.read(self.args.config)

    def configure_logging(self):
        logging.basicConfig(level=self.args.loglevel)
        if self.args.set_loglevel:
            for name, level in self.args.set_loglevel:
                logger = logging.getLogger(name)
                logger.setLevel(level.upper())

    def parse_args(self, args=None):
        return self.parser.parse_args(args=args)

    def create_overrides(self):
        return {}

    def process_overrides(self):
        for cli, cfgspec in self.overrides.items():
            section, option = cfgspec
            value = getattr(self.args, cli)

            if value is not None:
                if section not in self.config:
                    self.config.add_section(section)

                self.config.set(section, option, value)

    def create_parser(self):
        p = argparse.ArgumentParser()

        p.add_argument('--config', '-f',
                       default='kcam.conf')

        g = p.add_argument_group('Logging options')
        g.add_argument('--verbose', '-v',
                       action='store_const',
                       const='INFO',
                       dest='loglevel')
        g.add_argument('--debug', '-d',
                       action='store_const',
                       const='DEBUG',
                       dest='loglevel')
        g.add_argument('--set-loglevel', '-l',
                       action='append',
                       default=[],
                       metavar='LOGGER=LEVEL',
                       type=KeyValueArgument)

        p.set_defaults(loglevel='WARNING')

        return p
