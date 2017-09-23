import datetime

from kcam import observer


class Stopwatch(observer.Observable):
    def start(self):
        self.time_start = datetime.datetime.now()

    def stop(self):
        delta = datetime.datetime.now() - self.time_start
        self.notify_observers(delta.total_seconds())
        return delta
