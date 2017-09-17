#!/usr/bin/env python

import sys

from setuptools import setup

PY2 = sys.version_info[0] == 2
install_requires = [
    'six>=1.10.0',
]

if PY2:
    install_requires.append('ipaddress>=1.0.18')


setup(
    name='xmpp-backends',
    version='0.4.1',
    description='A set of classes with common interfaces to communicate with XMPP servers.',
    author='Mathias Ertl',
    author_email='mati@jabber.at',
    url='https://github.com/mathiasertl/xmpp-backends',
    packages=[
        'xmpp_backends',
        'xmpp_backends.django',
    ],
    license="GNU General Public License (GPL) v3",
    install_requires=install_requires,
    test_suite='tests',
    classifiers=[
        "Development Status :: 4 - Beta",
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
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications :: File Sharing",
    ],
    long_description="""A small python library providing a common interface for communicating with
the administration interfaces of various Jabber/XMPP servers."""
)
