# -*- coding: utf-8 -*-
#
# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends.  If
# not, see <http://www.gnu.org/licenses/>.

import doctest
import unittest
from datetime import datetime

import pytz
from xmpp_backends.base import XmppBackendBase
from xmpp_backends.base import UserSession
from xmpp_backends.constants import CONNECTION_HTTP_BINDING
from xmpp_backends.constants import CONNECTION_XMPP

from .utils import CompatDoctestChecker

base = XmppBackendBase()


class TestDateTimeToTimestamp(unittest.TestCase):
    def test_no_tz(self):
        now = datetime(2000, 1, 5, 12, 20, 3)
        converted = base.datetime_to_timestamp(now)
        self.assertEqual(converted, 947074803)
        self.assertEqual(datetime.utcfromtimestamp(converted), now)

        now = datetime(2000, 7, 5, 12, 20, 3)
        self.assertEqual(base.datetime_to_timestamp(now), 962799603)

    def test_utc(self):
        # results should be identical to no_tz above, since UTC is the default
        now = pytz.utc.localize(datetime(2000, 1, 5, 12, 20, 3))
        converted = base.datetime_to_timestamp(now)
        self.assertEqual(converted, 947074803)
        self.assertEqual(pytz.utc.localize(datetime.utcfromtimestamp(converted)), now)

        now = pytz.utc.localize(datetime(2000, 7, 5, 12, 20, 3))
        converted = base.datetime_to_timestamp(now)
        self.assertEqual(converted, 962799603)
        self.assertEqual(pytz.utc.localize(datetime.utcfromtimestamp(converted)), now)

    def test_vienna(self):
        # results are now different because this is a different TZ
        tz = pytz.timezone('Europe/Vienna')
        now = tz.localize(datetime(2000, 1, 5, 12, 20, 3))
        converted = base.datetime_to_timestamp(now)
        self.assertEqual(converted, 947071203)
        self.assertEqual(pytz.utc.localize(datetime.utcfromtimestamp(converted)), now)

        now = tz.localize(datetime(2000, 7, 5, 12, 20, 3))
        converted = base.datetime_to_timestamp(now)
        self.assertEqual(converted, 962792403)
        self.assertEqual(pytz.utc.localize(datetime.utcfromtimestamp(converted)), now)


class TestUserSessions(unittest.TestCase):
    def test_str(self):
        session = UserSession(base, 'user', 'example.com', 'resource',
                              priority=0, ip_address='127.0.0.1', uptime=None, status='online',
                              status_text='I am online.', connection_type=CONNECTION_XMPP,
                              encrypted=True, compressed=False)
        self.assertEqual(str(session), 'user@example.com/resource')

    def test_repr(self):
        session = UserSession(base, 'user', 'example.com', 'resource',
                              priority=0, ip_address='127.0.0.1', uptime=None, status='online',
                              status_text='I am online.', connection_type=CONNECTION_XMPP,
                              encrypted=True, compressed=False)
        self.assertEqual(repr(session), '<UserSession: user@example.com/resource>')

    def test_eq(self):
        session_a = UserSession(base, 'user', 'example.com', 'resource',
                                priority=0, ip_address='127.0.0.1', uptime=None, status='online',
                                status_text='I am online.', connection_type=CONNECTION_XMPP,
                                encrypted=True, compressed=False)

        # user, domain, resource are identical
        session_b = UserSession(base, 'user', 'example.com', 'resource',
                                priority=10, ip_address='192.168.0.1', uptime=33, status='offline',
                                status_text='I am ffline.', connection_type=CONNECTION_HTTP_BINDING,
                                encrypted=False, compressed=True)

        self.assertEqual(session_a, session_b)

        # change the resource
        session_b.resource = 'new resource'
        self.assertNotEqual(session_a, session_b)

        # We can also compare other object
        self.assertNotEqual(session_a, 'foobar')

    def test_hash(self):
        sessions = set()

        session_a = UserSession(base, 'user', 'example.com', 'resource',
                                priority=0, ip_address='127.0.0.1', uptime=None, status='online',
                                status_text='I am online.', connection_type=CONNECTION_XMPP,
                                encrypted=True, compressed=False)
        sessions.add(session_a)
        self.assertEqual(len(sessions), 1)

        # user, domain, resource are identical
        session_b = UserSession(base, 'user', 'example.com', 'resource',
                                priority=10, ip_address='192.168.0.1', uptime=33, status='offline',
                                status_text='I am ffline.', connection_type=CONNECTION_HTTP_BINDING,
                                encrypted=False, compressed=True)
        sessions.add(session_b)
        self.assertEqual(len(sessions), 1)  # still one, since it has the same hash

        session_a.resource = 'new'
        sessions.add(session_b)
        self.assertEqual(len(sessions), 2)


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite('xmpp_backends.base', checker=CompatDoctestChecker()))
    return tests
