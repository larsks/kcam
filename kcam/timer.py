import threading
import time
import logging

LOG = logging.getLogger(__name__)


class DynamicTimer(threading.Thread):

    '''Call a function after a specified interval.  The update method
    can be used to extend the interval while the timer is running.'''

    def __init__(self, interval, function, limit=None, **kwargs):
        super(DynamicTimer, self).__init__(**kwargs)
        self.function = function
        self.interval = interval
        self.limit = limit
        self.expires_at = None

    def run(self):
        self.expires_at = time.time() + self.interval
        if self.limit:
            self.expires_limit = time.time() + self.limit

        LOG.debug('started timer %s', self)

        while True:
            sleeptime = self.expires_at - time.time()
            time.sleep(sleeptime)

            now = time.time()
            if now >= self.expires_at:
                LOG.debug('timer expired %s', self)
                break

            if self.limit and now >= self.expires_limit:
                LOG.debug('timer %s reached limit', self)
                break

        self.function()

    def update(self, extra):
        if not self.is_alive():
            self.interval += extra
            LOG.debug('+%d to inactive timer %s', extra, self)
        else:
            self.expires_at += extra
            LOG.debug('+%d to active timer %s', extra, self)

    def __str__(self):
        if self.expires_at is None:
            when = 'not started'
        else:
            when = time.strftime('%Y-%m-%d %H:%M:%S',
                                 time.localtime(self.expires_at))

        return '<DynamicTimer %s>' % (when,)
