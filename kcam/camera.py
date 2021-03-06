import datetime
import logging
import picamera
import queue
import threading

from pathlib import Path

from kcam import observer

LOG = logging.getLogger(__name__)


def fmt_path(path, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    return path.format(timestamp=timestamp)


class Camera(observer.Observable, threading.Thread):
    default_res_x = 800
    default_res_y = 600
    default_lead_time = 10
    default_datadir = '.'
    default_eventdir = '{timestamp:%Y/%m/%d/%H:%M:%S}'
    default_imagename = 'img-{timestamp:%H:%M:%S}-{{counter}}.jpg'
    default_videoname = 'vid-{timestamp:%H:%M:%S}.h264'
    default_interval = 2
    default_flip = False

    def __init__(self,
                 res_x=None,
                 res_y=None,
                 lead_time=None,
                 datadir=None,
                 eventdir=None,
                 imagename=None,
                 videoname=None,
                 interval=None,
                 flip=None,
                 **kwargs):

        super(Camera, self).__init__(**kwargs)

        res_x = res_x if res_x else self.default_res_x
        res_y = res_y if res_y else self.default_res_y
        flip = flip if flip is not None else self.default_flip
        lead_time = lead_time if lead_time is not None else self.default_lead_time

        self.datadir = Path(datadir if datadir else self.default_datadir)
        self.eventdir = Path(eventdir if eventdir else self.default_eventdir)
        self.imagename = imagename if imagename else self.default_imagename
        self.videoname = videoname if videoname else self.default_videoname
        self.interval = interval if interval else self.default_interval

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
        LOG.info('start camera thread')
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
        LOG.info('stop camera thread')

    def update(self, active):
        LOG.debug('received notification: %s', active)
        if active and not self.recording:
            self.control.put('active')
        elif not active and self.recording:
            self.control.put('idle')

    def create_eventdir(self, timestamp=None):
        path = Path(fmt_path(str(self.datadir / self.eventdir), timestamp))
        LOG.info('creating eventdir at %s', path)
        path.mkdir(parents=True, exist_ok=True)

        return path

    def start_capture(self):
        LOG.info('starting capture')

        self.recording = True
        event = datetime.datetime.now()

        path = self.create_eventdir(event)
        videoname = fmt_path(self.videoname, event)
        videopath = path / videoname
        imagename = fmt_path(self.imagename, event)
        imagepath = path / imagename

        with videopath.open('wb') as fd:
            self.stream.copy_to(fd)
            self.camera.split_recording(fd)

            for img in self.camera.capture_continuous(
                    str(imagepath), use_video_port=True):

                try:
                    msg = self.control.get(timeout=self.interval)
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
        self.notify_observers(dict(datadir=self.datadir,
                                   event=event,
                                   path=path))
