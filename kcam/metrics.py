import influxdb
import logging

from . import observer

LOG = logging.getLogger(__name__)


class MetricListener(observer.Observer):

    def __init__(self, client, name, tags=None):
        self.client = client
        self.name = name

        if tags is None:
            tags = {}

        self.tags = tags

    def update(self, arg):
        if not isinstance(arg, dict):
            arg = {'value': arg}

        LOG.debug('sending metric %s = %s', self.name, arg)
        self.client.write_points([
            dict(measurement=self.name,
                 tags=self.tags,
                 fields=arg)
        ])


class MetricConnection(influxdb.InfluxDBClient):
    default_database = 'kcam'

    def __init__(self,
                 host=None,
                 port=None,
                 database=None,
                 **kwargs):

        if host:
            kwargs['host'] = host
        if port:
            kwargs['port'] = port

        super(MetricConnection, self).__init__(**kwargs)

        database = database if database else self.default_database
        self.create_database(database)
        self.switch_database(database)

    def create_observer(self, name, tags=None):
        return MetricListener(self, name, tags=tags)
