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
import re
import unittest
from datetime import datetime

import pytz
import six
from xmpp_backends.base import XmppBackendBase

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


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite('xmpp_backends.base', checker=CompatDoctestChecker()))
    return tests
