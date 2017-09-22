import datetime
import errno
import logging
import os
import picamera
import queue
import threading

from kcam import observer

LOG = logging.getLogger(__name__)


def fmt_path(path, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    return path.format(timestamp=timestamp)


class Camera(observer.Observable, threading.Thread):

    def __init__(self,
                 res_x=800,
                 res_y=600,
                 lead_time=10,
                 datadir='{timestamp:%Y/%m/%d/%H-%M-%S}',
                 imagename='img-{timestamp:%H-%M-%S}-{{counter}}.jpg',
                 videoname='vid-{timestamp:%H-%M-%S}.h264',
                 image_interval=2,
                 flip=False,
                 **kwargs):

        super(Camera, self).__init__(**kwargs)

        self.datadir = datadir
        self.imagename = imagename
        self.videoname = videoname
        self.image_interval = image_interval
        self.camera = picamera.PiCamera()
        self.camera.resolution = (res_x, res_y)
        self.camera.hflip = self.camera.vflip = flip
        self.stream = picamera.PiCameraCircularIO(
            self.camera, seconds=lead_time)

        self.recording = False
        self.control = queue.Queue()
        self.flag_stop = False

    def stop(self):
        self.flag_stop = True
        self.control.put('stop')

    def run(self):
        LOG.info('enter camera thread')
        self.camera.start_recording(self.stream, format='h264')

        while not self.flag_stop:
            msg = self.control.get()
            LOG.debug('received msg in run: %s', msg)

            if msg == 'stop':
                break
            elif msg == 'active' and not self.recording:
                self.start_capture()
            else:
                LOG.error('unexpected message in queue: %s', msg)

        self.camera.stop_recording()
        LOG.info('exit camera thread')

    def update(self, active):
        LOG.debug('received notification: %s', active)
        if active and not self.recording:
            self.control.put('active')
        elif not active and self.recording:
            self.control.put('idle')

    def create_datadir(self, timestamp=None):
        path = fmt_path(self.datadir, timestamp)
        LOG.info('creating datadir at %s', path)

        try:
            os.makedirs(path)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        return path

    def start_capture(self):
        LOG.info('starting capture')

        self.recording = True
        started_at = datetime.datetime.now()

        path = self.create_datadir(started_at)
        videoname = fmt_path(self.videoname, started_at)
        videopath = os.path.join(path, videoname)
        imagename = fmt_path(self.imagename, started_at)
        imagepath = os.path.join(path, imagename)

        with open(videopath, 'wb') as fd:
            self.stream.copy_to(fd)
            self.camera.split_recording(fd)

            for img in self.camera.capture_continuous(
                    imagepath, use_video_port=True):

                try:
                    msg = self.control.get(timeout=self.image_interval)
                    if msg in ['idle', 'stop']:
                        LOG.debug('received message in start_capture: %s', msg)
                        break
                except queue.Empty:
                    continue

            self.stream.seek(0)
            self.stream.truncate()
            self.camera.split_recording(self.stream)

        self.recording = False
        LOG.info('finished capture')
        self.notify_observers(videopath)
