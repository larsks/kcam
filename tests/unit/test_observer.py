import unittest

from kcam import observer


class FakeObserver(observer.Observer):

    def __init__(self, **kwargs):
        super(FakeObserver, self).__init__(**kwargs)

    def update(self, arg):
        self.update_called = True
        self.update_called_with = arg


class TestObserver (unittest.TestCase):

    def test_add_observer(self):
        f = FakeObserver()
        obs = observer.Observable()
        obs.add_observer(f)

        assert f.update in obs.observers

    def test_remove_observer(self):
        obs = observer.Observable()
        f = FakeObserver()
        obs.add_observer(f)
        obs.delete_observer(f)

        assert f.update not in obs.observers
        assert len(obs.observers) == 0

    def test_clear_observers(self):
        obs = observer.Observable()
        obs.add_observer(FakeObserver())
        obs.add_observer(FakeObserver())
        obs.clear_observers()

        assert len(obs.observers) == 0

    def test_notify_observers(self):
        f = FakeObserver()
        obs = observer.Observable()
        obs.add_observer(f)
        obs.notify_observers(self)

        assert f.update_called
        assert f.update_called_with is self
