import abc
import logging
import threading

LOG = logging.getLogger(__name__)


def synchronized(func):
    def wrapper(self, *args, **kwargs):
        self.mutex.acquire()
        try:
            return func(self, *args, **kwargs)
        finally:
            self.mutex.release()

    return wrapper


class Synchronization(object):

    def __init__(self, *args, **kwargs):
        super(Synchronization, self).__init__(*args, **kwargs)
        self.mutex = threading.RLock()


class Observer(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def update(self, arg):
        pass


class Observable(Synchronization):

    def __init__(self, *args, **kwargs):
        super(Observable, self).__init__(*args, **kwargs)
        self.observers = set()

    @synchronized
    def add_observer(self, who, callback=None):
        if callback is None:
            callback = getattr(who, 'update')

        self.observers.add(callback)

    @synchronized
    def delete_observer(self, who, callback=None):
        if callback is None:
            callback = getattr(who, 'update')

        self.observers.remove(callback)

    @synchronized
    def clear_observers(self):
        self.observers = set()

    def notify_observers(self, arg=None):
        LOG.debug('sending notifications')
        with self.mutex:
            obs = list(self.observers)

        for observer in obs:
            LOG.debug('notifying %s', observer)
            observer(arg)


class Value(Observable):
    def __init__(self, initial_value=None, **kwargs):
        super(Value, self).__init__(**kwargs)
        self.value = initial_value

    def set(self, value):
        self.value = value
        self.notify_observers(value)
