import logging
import multiprocessing
import pathlib
import subprocess

LOG = logging.getLogger(__name__)


class Encoder(multiprocessing.Process):
    def __init__(self, **kwargs):
        super(Encoder, self).__init__(**kwargs)

        self.q = multiprocessing.Queue()

    def update(self, path):
        self.q.put(('encode', path))

    def stop(self):
        self.q.put(('stop', 'stop'))

    def run(self):
        LOG.info('start encoding process')
        while True:
            try:
                command, arg = self.q.get()
            except KeyboardInterrupt:
                break
            LOG.debug('received message: %s', command)

            if command == 'stop':
                break
            elif command == 'encode':
                self.encode(arg)

        LOG.info('stop encoding process')

    def encode(self, path):
        path = pathlib.Path(path)
        outpath = path.with_suffix('.mp4')
        try:
            subprocess.check_call([
                'ffmpeg', '-f', 'h264', '-i', str(path),
                '-c:v', 'copy', str(outpath),
            ])
            path.unlink()
        except subprocess.CalledProcessError as err:
            if outpath.is_file():
                outpath.unlink()
            LOG.error('failed to encode file %s: %s', path, err)
