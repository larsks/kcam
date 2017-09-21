from setuptools import setup

setup(
    name='kcam',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@oddbit.com',
    url='https://github.com/larsks/kcam',
    packages=['kcam'],
    install_requires=[
        'RPi.GPIO',
        'Adafruit_Python_DHT',
    ],
    entry_points={
        'console_scripts': [
            'kcam = kcam.main:main',
        ],
    }
)
