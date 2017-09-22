import threading
import time

from kcam import observer


class Blink(observer.Observable, threading.Thread):

    def __init__(self, interval=1, **kwargs):
        super(Blink, self).__init__(daemon=True, **kwargs)

        if isinstance(interval, tuple):
            self.on_interval, self.off_interval = interval
        else:
            self.on_interval = self.off_interval = interval

    def run(self):
        while True:
            self.notify_observers(1)
            time.sleep(self.on_interval)
            self.notify_observers(0)
            time.sleep(self.off_interval)
