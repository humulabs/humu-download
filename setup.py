"""
|Downloads|

humu-download
=============

CLI to download `Humu`_ data series.

.. _Humu: http://www.humu.io/

.. |Downloads| image:: https://img.shields.io/pypi/dm/humu-download.svg
   :target: https://pypi.python.org/pypi/humu-download

"""
import os
import sys

from setuptools import setup, find_packages

setup(
    name='humu-download',
    version='1.1.1',
    description='CLI and curses UI for dowloading Humu data files',
    long_description=__doc__,
    url='https://github.com/humulabs/humu-download/blob/master/README.rst',
    author='Michael Keirnan',
    author_email='michael@keirnan.com',
    packages=['humu_download'],
    package_dir={'': '.'},
    install_requires=[
        'docopt',
        'urwid_timed_progress>=1.1.1',
        'requests',
        'pandas',
    ],
    entry_points={
        'console_scripts': ['humu-download=humu_download.main:main'],
    },
    tests_require=[
        'pep8',
    ],
    platforms='any',
    license='MIT',
    keywords="arduino iot sd serial",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
