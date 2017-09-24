import datetime
import jinja2
import logging
import multiprocessing
import os
import subprocess

from pathlib import Path

LOG = logging.getLogger(__name__)


def generate_thumbnail(src, dest, res_x=375, res_y=500):
    out = subprocess.check_output([
        'convert',
        str(src),
        '-geometry', '{}x{}'.format(res_x, res_y),
        str(dest)])

    out


def date_from_path(path):
    if len(str(path).split('/')) != 4:
        raise ValueError('path "%s" must have four components' % path)

    year, month, day = (int(x) for x in str(path.parent).split('/'))
    hour, minute, second = (int(x) for x in str(path.name).split(':'))
    return datetime.datetime(
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second
    )


class Webify(multiprocessing.Process):
    def __init__(self,
                 datadir=None,
                 templatedir=None,
                 **kwargs):
        super(Webify, self).__init__(**kwargs)
        self.datadir = Path(datadir)

        loaders = []
        if templatedir:
            loaders.append(jinja2.FileSystemLoader(templatedir))
        loaders.append(jinja2.PackageLoader('kcam', 'templates'))

        self.env = jinja2.Environment(
            loader=jinja2.ChoiceLoader(loaders),
        )
        self.tmpl_eventlist = self.env.get_template('eventlist.html')
        self.tmpl_event = self.env.get_template('event.html')

    def run(self):
        events = self.discover_events()
        for event in events:
            self.process_event(*event)

        self.generate_event_list(events)

    def generate_event_list(self, events):
        LOG.info('generating event list')
        with (self.datadir/'index.html').open('w') as fd:
            fd.write(self.tmpl_eventlist.render(
                title='Event list',
                events=sorted(events),
            ))

    def discover_events(self):
        events = []
        for root, dirs, files in os.walk(str(self.datadir)):
            root = Path(root).relative_to(self.datadir)
            if len(str(root).split('/')) != 4:
                continue

            event = date_from_path(root)
            events.append((event, root))

        return events

    def get_media_info(self, media):
        media_info = []
        for thing in media:
            media_info.append({
                'fspath': thing,
                'path': thing.relative_to(self.datadir),
                'stat': thing.stat(),
            })

        return media_info

    def annotate_thumbnails(self, image_info):
        for img in image_info:
            thumb = (img['fspath'].parent/
                     (img['fspath'].stem + '-thumb' + img['fspath'].suffix))

            img['thumb_fspath'] = thumb
            img['thumb'] = thumb.relative_to(self.datadir)

    def generate_thumbnails(self, image_info):
        for img in image_info:
            if img['thumb_fspath'].is_file():
                continue

            try:
                generate_thumbnail(img['fspath'], img['thumb_fspath'])
            except subprocess.CalledProcessError:
                LOG.warning('failed to create thumbnail for %s',
                            img['fspath'])

    def process_event(self, when, path):
        images = [x for x in (self.datadir/path).glob('*.jpg')
                  if 'thumb' not in str(x)]
        videos = [x for x in (self.datadir/path).glob('*.mp4')
                  if 'thumb' not in str(x)]

        LOG.debug('for event %s found %d images, %d videos',
                  path, len(images), len(videos))

        image_info = self.get_media_info(images)
        video_info = self.get_media_info(videos)

        self.annotate_thumbnails(image_info)
        self.generate_thumbnails(image_info)

        LOG.info('generating index.html for event %s', path)
        with (self.datadir/path/'index.html').open('w') as fd:
            fd.write(self.tmpl_event.render(
                event=when,
                images=sorted(image_info, key=lambda x: x['stat'].st_mtime),
                videos=sorted(video_info, key=lambda x: x['stat'].st_mtime),
            ))


if __name__ == '__main__':
    logging.basicConfig(level="DEBUG")
    w = Webify('web')
    w.start()
