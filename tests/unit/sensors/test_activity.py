import logging
import threading
import time
import unittest
import unittest.mock

from kcam.sensors import activity
from kcam import observer


class FakeSensor(observer.Observable):

    def notify(self):
        self.notify_observers(True)


class FakeObserver(observer.Observer):

    def __init__(self, **kwargs):
        super(FakeObserver, self).__init__(**kwargs)
        self.update_called = 0
        self.update_called_with = []
        self.condition = threading.Event()

    def update(self, arg):
        logging.info('fakeobserver update')
        self.update_called += 1
        self.update_called_with.append(arg)
        self.condition.set()
        self.condition.clear()


class TestActivity (unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level='DEBUG')

    def test_create(self):
        f = FakeSensor()
        a = activity.ActivitySensor(f)

        assert a.source == f

    def test_start(self):
        f = FakeSensor()
        a = activity.ActivitySensor(f)
        a.start()

        assert a.update in f.observers

    def test_propogate_notify(self):
        f = FakeSensor()
        o = FakeObserver()
        a = activity.ActivitySensor(f, interval=1, cooldown=1)
        a.add_observer(o)
        a.start()

        f.notify()
        called = o.condition.wait(5)

        assert called

    def test_return_to_idle(self):
        f = FakeSensor()
        a = activity.ActivitySensor(f, interval=1, cooldown=1)

        c1 = threading.Event()
        c2 = threading.Event()

        def cond_iter(*args):
            yield c1.set()
            yield c2.set()

        o = unittest.mock.MagicMock()
        o.update.side_effect = iter(cond_iter())
        a.add_observer(o)
        a.start()

        f.notify()
        r1 = c1.wait(5)
        r2 = c2.wait(5)

        assert r1 and r2
        assert o.update.call_args_list == [unittest.mock.call(True),
                                           unittest.mock.call(False)]
