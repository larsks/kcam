import logging

from kcam.timer import DynamicTimer
from kcam import observer

LOG = logging.getLogger(__name__)

STATE_IDLE = 0
STATE_ACTIVE = 1
STATE_COOLDOWN = 3


class ActivitySensor(observer.Observable, observer.Observer):
    def __init__(self, source,
                 interval=20,
                 update=10,
                 limit=120,
                 cooldown=30,
                 **kwargs):

        super(ActivitySensor, self).__init__(**kwargs)

        self.source = source
        self.active = 0
        self.interval = interval
        self.limit = limit
        self.cooldown = cooldown

    def start(self):
        LOG.info('start activity sensor')
        self.source.add_observer(self)

    def stop(self):
        LOG.info('stop activity sensor')
        self.source.delete_observer(self)

    def update(self, arg):
        if self.active == STATE_COOLDOWN:
            LOG.debug('ignoring motion during cooldown period')
            return

        if arg:
            if self.active == STATE_ACTIVE:
                self.continue_active()
            elif self.active == STATE_IDLE:
                self.start_active()

    def start_active(self):
        LOG.debug('start activity')
        self.active = STATE_ACTIVE
        self.notify_observers(True)

        self.timer = DynamicTimer(
            interval=self.interval,
            function=self.end_active,
            limit=self.limit)
        self.timer.start()

    def continue_active(self):
        LOG.debug('continue activity')
        self.timer.extend(self.interval)

    def end_active(self):
        LOG.debug('end activity')
        self.active = STATE_COOLDOWN
        self.notify_observers(False)

        LOG.debug('cooldown for %d seconds', self.cooldown)
        self.timer = DynamicTimer(
            interval=self.cooldown,
            function=self.end_cooldown)
        self.timer.start()

    def end_cooldown(self):
        LOG.info('end cooldown')
        self.active = STATE_IDLE
