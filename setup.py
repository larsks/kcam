from setuptools import setup, find_packages

setup(
    name='kcam',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@oddbit.com',
    url='https://github.com/larsks/kcam',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'kcam = kcam.main:main',
            'kcam-update-html = kcam.main:update_html',
            'kcam-tempd = kcam.cmd.tempd:main',
        ],
    }
)
