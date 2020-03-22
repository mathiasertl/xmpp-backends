# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends. If not, see
# <http://www.gnu.org/licenses/>.

from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time

from django.core.cache import cache
from django.test import TestCase

from xmpp_backends.base import UserNotFound
from xmpp_backends.django.fake_xmpp.backend import FakeXMPPBackend
from xmpp_backends.dummy import DummyBackend


class BackendTestMixin:
    api_version = (1, 0, )
    domain1 = 'example.com'
    domain2 = 'example.net'
    domains = [domain1, domain2]
    node1 = 'user1'
    password1 = 'password1'

    def setUp(self):
        cache.clear()
        super().setUp()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_api_version(self):
        self.assertEqual(self.backend.api_version, self.api_version)
        self.assertEqual(self.backend.get_api_version(), self.api_version)

    def test_all_domains(self):
        self.assertEqual(self.backend.all_domains(), self.domains)

    def test_create_user(self):
        self.assertEqual(self.backend.all_users(self.domain1), set())
        self.assertEqual(self.backend.all_users(self.domain2), set())

        self.backend.create_user(self.node1, self.domain1, self.password1)
        self.assertEqual(self.backend.all_users(self.domain1), {self.node1, })
        self.assertEqual(self.backend.all_users(self.domain2), set())

    def test_last_activity(self):
        with self.assertRaisesRegex(UserNotFound, r'%s@%s' % (self.node1, self.domain1)):
            self.backend.get_last_activity(self.node1, self.domain1)

        with freeze_time('2020-03-22') as frozen:
            self.backend.create_user(self.node1, self.domain1, self.password1)

            self.assertEqual(self.backend.get_last_activity(self.node1, self.domain1),
                             datetime(2020, 3, 22))

            # move time ahead two minutes
            frozen.tick(delta=timedelta(seconds=120))
            self.assertEqual(self.backend.get_last_activity(self.node1, self.domain1),
                             datetime(2020, 3, 22))

            # set last activity to one minute ago
            past = datetime(2020, 3, 22, 0, 1)
            self.backend.set_last_activity(self.node1, self.domain1, timestamp=past)
            self.assertEqual(self.backend.get_last_activity(self.node1, self.domain1),
                             datetime(2020, 3, 22, 0, 1))

            # set last activity to now
            self.backend.set_last_activity(self.node1, self.domain1)
            self.assertEqual(self.backend.get_last_activity(self.node1, self.domain1),
                             datetime(2020, 3, 22, 0, 2))


class FakeXMPPBackendTestCase(BackendTestMixin, TestCase):
    def setUp(self):
        self.backend = FakeXMPPBackend(self.domains)
        super().setUp()


class DummyBackendTestCase(BackendTestMixin, TestCase):
    def setUp(self):
        self.backend = DummyBackend(self.domains)
        super().setUp()
