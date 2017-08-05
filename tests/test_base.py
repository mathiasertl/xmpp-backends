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

import unittest
from datetime import datetime

from xmpp_backends.base import XmppBackendBase

base = XmppBackendBase()


class TestDateTimeToTimestamp(unittest.TestCase):
    def test_no_tz(self):
        now = datetime(2000, 3, 5, 12, 20, 3)
        self.assertEqual(base.datetime_to_timestamp(now), 952255203)
