import datetime
import logging

from kcam import observer

LOG = logging.getLogger(__name__)


class Stopwatch(observer.Observable):
    def start(self):
        self.time_start = datetime.datetime.now()
        LOG.debug('started stopwatch @ %s', self.time_start)

    def stop(self):
        delta = datetime.datetime.now() - self.time_start
        delta_seconds = delta.total_seconds()
        LOG.debug('stopped stopwatch after %f', delta_seconds)
        self.notify_observers(delta_seconds)
        return delta
