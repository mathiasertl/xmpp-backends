#!/usr/bin/env python

import os
import sys

from setuptools import setup
from setuptools.command.test import test

PY2 = sys.version_info[0] == 2
install_requires = [
    'six>=1.10.0',
]

if PY2:
    install_requires.append('ipaddress>=1.0.18')


class django_test(test):
    def run(self):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
        sys.path.insert(0, '.')
        import django
        django.setup()
        test.run(self)  # super() fails, LOL


setup(
    name='xmpp-backends',
    version='0.7.0',
    description='A set of classes with common interfaces to communicate with XMPP servers.',
    author='Mathias Ertl',
    author_email='mati@jabber.at',
    url='https://github.com/mathiasertl/xmpp-backends',
    packages=[
        'xmpp_backends',
        'xmpp_backends.django',
        'xmpp_backends.django.fake_xmpp',
        'xmpp_backends.django.fake_xmpp.migrations',
    ],
    cmdclass={
        'test': django_test,
    },
    license="GNU General Public License (GPL) v3",
    install_requires=install_requires,
    test_suite='tests',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        #"Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications :: File Sharing",
    ],
    long_description="""A small python library providing a common interface for communicating with
the administration interfaces of various Jabber/XMPP servers."""
)
