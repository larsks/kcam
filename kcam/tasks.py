import jinja2
import logging
import os
import subprocess
from pathlib import Path

from kcam.util import date_from_path

LOG = logging.getLogger(__name__)


def thumbnail_path(path):
    return path.parent / (path.stem + '-thumb' + path.suffix)


class EncodeVideo(object):
    def __call__(self, arg):
        LOG.debug('start encode video task @ %s', arg['path'])
        path = Path(arg['path'])

        failures = 0
        for video in path.glob('*.h264'):
            outpath = video.with_suffix('.mp4')
            try:
                subprocess.check_call([
                    'ffmpeg', '-f', 'h264', '-i', str(video),
                    '-c:v', 'copy', str(outpath),
                ])
                video.unlink()
            except subprocess.CalledProcessError as err:
                LOG.error('failed to encode file %s: %s', video, err)
                if outpath.is_file():
                    outpath.unlink()
                failures += 1

        LOG.debug('finish encode video task w/ %d failures', failures)
        return failures == 0


class GenerateThumbnails(object):
    '''Generate thumbnails for a single event'''

    def __init__(self, res_x=180, res_y=240):
        self.res_x = res_x
        self.res_y = res_y

    def __call__(self, arg):
        LOG.debug('start generate thumbnail task @ %s', arg['path'])
        path = Path(arg['path'])

        failures = 0
        for image in path.glob('*.jpg'):
            thumb = thumbnail_path(image)
            try:
                subprocess.check_call([
                    'convert',
                    str(image),
                    '-geometry', '{}x{}'.format(self.res_x, self.res_y),
                    str(thumb)])
            except subprocess.CalledProcessError as err:
                LOG.error('failed to generate thumbnail for %s: %s',
                          image, err)
                failures += 1

        LOG.debug('finish generate thumbnail task w/ %d failures', failures)
        return failures == 0


class TemplateProcessor(object):
    def __init__(self, templatedir=None):
        self.templatedir = templatedir

    def create_env(self):
        # Doing this in __init__ was causing problems with
        # multiprocessing apparently due to the weakref's
        # that are used in jinja2.
        loaders = []
        if self.templatedir:
            loaders.append(jinja2.FileSystemLoader(self.templatedir))
        loaders.append(jinja2.PackageLoader('kcam', 'templates'))

        self.env = jinja2.Environment(
            loader=jinja2.ChoiceLoader(loaders),
        )


class UpdateEventHTML(TemplateProcessor):
    '''Generate index.html for a single event.'''

    def get_media_info(self, media, datadir):
        '''stat each path in media and compute a thumbnail name'''
        media_info = []
        for path in media:
            LOG.debug('getting media information for %s', path)
            media_info.append({
                'path': path,
                'thumb': thumbnail_path(path),
                'stat': path.stat(),
            })

        return media_info

    def __call__(self, arg):
        LOG.debug('start update event html task @ %s', arg['path'])
        path = Path(arg['path'])
        datadir = Path(arg['datadir'])

        videos = path.glob('*.mp4')
        images = [x for x in path.glob('*.jpg')
                  if 'thumb' not in str(x)]

        video_info = self.get_media_info(videos, datadir)
        image_info = self.get_media_info(images, datadir)

        self.create_env()
        self.template = self.env.get_template('event.html')

        with (path / 'index.html').open('w') as fd:
            fd.write(self.template.render(
                datadir=arg['datadir'],
                event=arg['event'],
                videos=sorted(video_info, key=lambda x: x['stat'].st_mtime),
                images=sorted(image_info, key=lambda x: x['stat'].st_mtime),
            ))

        return True


class UpdateEventListHTML(TemplateProcessor):
    '''Generate the main event listing'''

    def __call__(self, arg):
        LOG.debug('start update event list html task')
        datadir = Path(arg['datadir'])
        events = []

        for root, dirs, files in os.walk(str(datadir)):
            root = Path(root)
            relpath = root.relative_to(datadir)
            LOG.debug('checking %s (%s)', root, relpath)

            if len(str(relpath).split('/')) != 4:
                continue

            event = date_from_path(relpath)
            events.append((event, root))

        self.create_env()
        self.template = self.env.get_template('eventlist.html')

        with (datadir / 'index.html').open('w') as fd:
            fd.write(self.template.render(
                datadir=datadir,
                title='Event list',
                events=sorted(events),
            ))

        return True
