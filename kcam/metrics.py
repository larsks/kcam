import influxdb
import logging

from . import observer

LOG = logging.getLogger(__name__)


class MetricListener(observer.Observer):

    def __init__(self, client, name, tags=None):
        self.client = client
        self.name = name
        self.tags = tags

    def update(self, arg):
        if not isinstance(arg, dict):
            raise ValueError('update argument must be a dictionary')

        LOG.info('metric %s = %s', self.name, arg)
        self.client.write_points([
            dict(measurement=self.name,
                 tags=self.tags,
                 fields=arg)
        ])


class MetricConnection(influxdb.InfluxDBClient):

    def __init__(self,
                 database='kcam',
                 **kwargs):

        super(MetricConnection, self).__init__(**kwargs)
        self.create_database(database)
        self.switch_database(database)

    def create_observer(self, name, tags=None):
        return MetricListener(self, name, tags=tags)
