import threading
import time
import logging

LOG = logging.getLogger(__name__)


class DynamicTimer(threading.Thread):

    '''Call a function after a specified interval.  The update method
    can be used to extend the interval while the timer is running.'''

    def __init__(self, interval, function, limit=None, **kwargs):
        super(DynamicTimer, self).__init__(daemon=True, **kwargs)
        self.function = function
        self.interval = interval
        self.limit = limit
        self.started_at = None
        self.expires_at = None
        self.evt_stop = threading.Event()

    def stop(self):
        self.evt_stop.set()

    def run(self):
        now = time.time()

        self.started_at = now
        self.expires_at = now + self.interval
        if self.limit:
            self.expires_limit = now + self.limit

        LOG.debug('started timer %s', self)

        while True:
            sleeptime = self.expires_at - time.time()
            if self.evt_stop.wait(sleeptime):
                LOG.info('stopping timer %s', self)
                return

            now = time.time()
            if now >= self.expires_at:
                LOG.debug('timer %s expired', self)
                break

            if self.limit and now >= self.expires_limit:
                LOG.debug('timer %s reached limit', self)
                break

        self.function()

    def extend(self, extra):
        if not self.is_alive():
            raise ValueError('attempt to update idle timer')

        self.expires_at = max(self.expires_at,
                              time.time() + extra)
        LOG.debug('extended timer %s', self)

    def __str__(self):
        if self.expires_at is None:
            when = 'not started'
        else:
            when = time.strftime('%Y-%m-%d %H:%M:%S',
                                 time.localtime(self.expires_at))

        return '<DynamicTimer %s>' % (when,)
