import logging

from kcam.timer import DynamicTimer
from kcam import observer

LOG = logging.getLogger(__name__)

STATE_IDLE = 0
STATE_ACTIVE = 1
STATE_COOLDOWN = 3


class ActivitySensor(observer.Observable, observer.Observer):
    default_interval = 20
    default_extend = 20
    default_limit = 120
    default_cooldown = 30

    def __init__(self,
                 interval=None,
                 extend=None,
                 limit=None,
                 cooldown=None,
                 **kwargs):

        super(ActivitySensor, self).__init__(**kwargs)

        self.interval = interval if interval else self.default_interval
        self.limit = limit if limit else self.default_limit
        self.extend = extend if extend else self.default_extend
        self.cooldown = cooldown if cooldown else self.default_cooldown

        self.active = STATE_IDLE

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
        self.notify_observers(1)

        self.timer = DynamicTimer(
            interval=self.interval,
            function=self.end_active,
            limit=self.limit)
        self.timer.start()

    def continue_active(self):
        LOG.debug('continue activity')
        self.timer.extend(self.extend)

    def end_active(self):
        LOG.debug('end activity')
        self.active = STATE_COOLDOWN
        self.notify_observers(0)

        LOG.debug('cooldown for %d seconds', self.cooldown)
        self.timer = DynamicTimer(
            interval=self.cooldown,
            function=self.end_cooldown)
        self.timer.start()

    def end_cooldown(self):
        LOG.info('end cooldown')
        self.active = STATE_IDLE

    @property
    def value(self):
        return self.active == STATE_ACTIVE
