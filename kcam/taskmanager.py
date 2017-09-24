import logging
import multiprocessing
import queue
import signal
import threading

from kcam import observer

LOG = logging.getLogger(__name__)


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class TaskManager(observer.Synchronization, threading.Thread):

    def __init__(self, workers=None, **kwargs):
        super(TaskManager, self).__init__(**kwargs)
        workers = workers if workers else multiprocessing.cpu_count()

        self.tasks = []
        self.pool = multiprocessing.Pool(processes=workers,
                                         initializer=init_worker)
        self.q = queue.Queue()
        self.flag_stop = False

    @observer.synchronized
    def add_task(self, task):
        self.tasks.append(task)

    @observer.synchronized
    def remove_task(self, task):
        self.tasks.remove(task)

    @observer.synchronized
    def clear_tasks(self):
        self.tasks = []

    def stop(self):
        self.flag_stop = True

    def run(self):
        LOG.info('starting task manager')

        while not self.flag_stop:
            try:
                args = self.q.get(timeout=1)
            except queue.Empty:
                continue

            with self.mutex:
                taskiter = iter(self.tasks[:])

            while not self.flag_stop:
                try:
                    taskspec = next(taskiter)
                except StopIteration:
                    break

                if not self.run_parallel_tasks(taskspec, args):
                    LOG.error('aborting pipeline')
                    break

        LOG.info('waiting for active tasks to complete')
        self.pool.close()
        self.pool.join()
        LOG.info('stop task manager')

    def run_parallel_tasks(self, tasks, args):
        res = [self.pool.apply_async(task, args)
               for task in tasks]

        has_failures = False
        resiter = iter(res)
        while not self.flag_stop:
            try:
                taskresult = next(resiter)
            except StopIteration:
                break

            try:
                res = taskresult.get()
                if not res:
                    LOG.error('task execution failed (%s)', res)
                    has_failures = True
            except Exception:
                LOG.error('task execution failed', exc_info=True)
                has_failures = True

        return not has_failures

    def update(self, *args):
        self.q.put(args)
