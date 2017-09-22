import threading
import unittest
import unittest.mock

from kcam.sensors import activity
from kcam import observer


class FakeSensor(observer.Observable):

    def notify(self):
        self.notify_observers(True)


class TestActivity (unittest.TestCase):

    def setUp(self):
        observer = unittest.mock.MagicMock()
        observer.conditions = [threading.Event(),
                               threading.Event()]

        def cond_iter():
            for c in observer.conditions:
                yield c.set()
                print('YIELD!')

        observer.update.side_effect = iter(cond_iter())
        self.observer = observer

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
        a = activity.ActivitySensor(f, interval=1, cooldown=1)
        a.add_observer(self.observer)
        a.start()

        f.notify()
        called = self.observer.conditions[0].wait(5)

        assert called

    def test_return_to_idle(self):
        f = FakeSensor()
        a = activity.ActivitySensor(f, interval=1, cooldown=1)
        a.add_observer(self.observer)
        a.start()

        f.notify()
        r1 = self.observer.conditions[0].wait(5)
        r2 = self.observer.conditions[1].wait(5)

        assert r1 and r2
        expected = [unittest.mock.call(True), unittest.mock.call(False)]
        assert self.observer.update.call_args_list == expected
