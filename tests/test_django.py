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

from django.core.cache import cache
from django.test import TestCase

from xmpp_backends.django.auth_backends import XmppBackendBackend
from xmpp_backends.django import xmpp_backend
from xmpp_backends.django.models import XmppBackendUser

from .test_app.models import XmppUser


class XmppBackendUserTestCase(TestCase):
    def setUp(self):
        cache.clear()
        super().setUp()

    def tearDown(self):
        cache.clear()
        super().setUp()

    def test_basic(self):
        pwd = 'dummy'
        u = XmppUser.objects.create(jid='user@example.com')
        self.assertEqual(u.node, 'user')
        self.assertEqual(u.domain, 'example.com')
        self.assertEqual(u.get_short_name(), 'user')
        self.assertFalse(u.exists())
        self.assertFalse(xmpp_backend.user_exists(u.node, u.domain))

        xmpp_backend.create_user(u.node, u.domain, pwd)
        self.assertTrue(u.exists())
        self.assertTrue(xmpp_backend.user_exists(u.node, u.domain))

    def test_password(self):
        pwd = 'password'
        pwd2 = 'password2'
        u = XmppUser.objects.create(jid='user@example.com')
        self.assertFalse(u.check_password(pwd))
        self.assertFalse(u.check_password(pwd2))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd2))

        xmpp_backend.create_user(u.node, u.domain, pwd)
        self.assertTrue(u.check_password(pwd))
        self.assertFalse(u.check_password(pwd2))
        self.assertTrue(xmpp_backend.check_password(u.node, u.domain, pwd))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd2))

        u.set_password(pwd2)
        self.assertFalse(u.check_password(pwd))
        self.assertTrue(u.check_password(pwd2))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd))
        self.assertTrue(xmpp_backend.check_password(u.node, u.domain, pwd2))

    def test_set_empty_password(self):
        pwd = 'password'
        u = XmppUser.objects.create(jid='user@example.com')
        xmpp_backend.create_user(u.node, u.domain, pwd)
        self.assertTrue(u.check_password(pwd))
        self.assertTrue(xmpp_backend.check_password(u.node, u.domain, pwd))

        u.set_password(None)
        self.assertFalse(u.check_password(pwd))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd))

    def test_set_unusable_password(self):
        pwd = 'password'
        u = XmppUser.objects.create(jid='user@example.com')
        xmpp_backend.create_user(u.node, u.domain, pwd)
        self.assertTrue(u.check_password(pwd))
        self.assertTrue(xmpp_backend.check_password(u.node, u.domain, pwd))

        u.set_unusable_password()
        self.assertFalse(u.check_password(pwd))
        self.assertFalse(xmpp_backend.check_password(u.node, u.domain, pwd))



class XmppBackendBackendTestCase(TestCase):
    pass
