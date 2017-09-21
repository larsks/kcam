import threading
import time
import unittest

from kcam import timer


class TestTimer (unittest.TestCase):

    def log_timer_expire(self):
        self.timer_expired_at = time.time()

    def pre_timer(self):
        self.condition = threading.Event()

    def post_timer(self):
        self.condition.set()

    def test_timer_simple(self):
        interval = 5

        self.pre_timer()
        t = timer.DynamicTimer(interval,
                               self.post_timer)
        t.start()

        t0 = time.time()
        self.condition.wait(interval * 2)
        t1 = time.time()

        assert int(interval) == int(t1-t0)

    def test_timer_update(self):
        interval = 5

        self.pre_timer()
        t = timer.DynamicTimer(interval,
                               self.post_timer)
        t.start()
        t.update(interval)

        t0 = time.time()
        self.condition.wait(interval * 3)
        t1 = time.time()

        assert int(interval) * 2 == int(t1-t0)
