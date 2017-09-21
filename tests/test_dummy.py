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

from django.test import TestCase

from xmpp_backends.base import UserNotFound
from xmpp_backends.dummy import DummyBackend


class TestSessionsBackend(TestCase):
    def setUp(self):
        self.backend = DummyBackend()

    def test_wrong_user(self):
        self.assertEquals(self.backend.all_sessions(), set())
        with self.assertRaisesRegex(UserNotFound, 'wrong@example.com/rsrc'):
            self.backend.start_user_session('wrong', 'example.com', 'rsrc')
        self.assertEquals(self.backend.all_sessions(), set())

    def test_session(self):
        node = 'user'
        domain = 'example.com'
        rsrc = 'resource'
        self.backend.create_user(node, domain, 'password')
        self.assertEquals(self.backend.all_sessions(), set())

        self.backend.start_user_session(node, domain, rsrc)
        self.assertEquals(self.backend.all_sessions(), set())

    def tearDown(self):
        self.backend.module.clear()
