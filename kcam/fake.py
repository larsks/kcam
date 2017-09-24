import time
import threading

from kcam import observer


class FakeActivitySensor(observer.Observable, threading.Thread):
    stopwatch = observer.Value()

    def run(self):
        time.sleep(5)
        self.notify_observers(1)
        time.sleep(10)
        self.notify_observers(0)

    def update(self, arg):
        pass
