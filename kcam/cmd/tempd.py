import signal

from kcam.common import Application
from kcam.metrics import MetricConnection
from kcam.sensors.temperature import TemperatureSensor


class SensorApplication(Application):
    def required_config_sections(self):
        sections = super(SensorApplication, self).required_config_sections()
        return sections + ['metrics', 'sensor:temperature']

    def create_overrides(self):
        overrides = super(SensorApplication, self).create_overrides()

        overrides.update({
            'device_type': ('sensor:temperature', 'temperature_devicetype'),
            'read_interval': ('sensor:temperature', 'temperature_interval'),
            'influxdb_host': ('metrics', 'metrics_host'),
            'influxdb_port': ('metrics', 'metrics_port'),
            'influxdb_database': ('metrics', 'metrics_database'),
            'influxdb_username': ('metrics', 'metrics_username'),
            'influxdb_password': ('metrics', 'metrics_password'),
        })

        return overrides

    def create_parser(self):
        p = super(SensorApplication, self).create_parser()

        g = p.add_argument_group('Sensor options')
        g.add_argument('--device-type')
        g.add_argument('--read-interval', '-i')

        g = p.add_argument_group('Metric options')
        g.add_argument('--influxdb-host', '-H')
        g.add_argument('--influxdb-port', '-P')
        g.add_argument('--influxdb-database', '-D')
        g.add_argument('--influxdb-username')
        g.add_argument('--influxdb-password')

        return p

    def main(self):
        self.metrics = MetricConnection(
            host=self.config['metrics'].get('metrics_host'),
            port=self.config['metrics'].getint('metrics_port'),
            database=self.config['metrics'].get('metrics_database'),
            username=self.config['metrics'].get('metrics_username'),
            password=self.config['metrics'].get('metrics_password'),
        )

        self.temp_sensor = TemperatureSensor(
            self.config.getint('sensor:temperature', 'temperature_pin'),
            devicetype=self.config['sensor:temperature'].get('temperature_devicetype'),
            interval=self.config['sensor:temperature'].get('temperature_interval'),
        )

        self.temp_sensor.temperature.add_observer(self.metrics.create_observer('temperature'))
        self.temp_sensor.humidity.add_observer(self.metrics.create_observer('humidity'))
        self.temp_sensor.start()

        try:
            signal.pause()
        except KeyboardInterrupt:
            self.temp_sensor.stop()
            self.temp_sensor.join()

app = SensorApplication()


def main():
    app.run()

if __name__ == '__main__':
    main()
