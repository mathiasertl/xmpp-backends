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

from django.test import TestCase

from xmpp_backends.django.models import XmppBackendUser
from xmpp_backends.django.auth_backends import XmppBackendBackend

from xmpp_backends.base import UserNotFound
from xmpp_backends.dummy import DummyBackend


class XmppBackendUserTestCase(TestCase):
    def test_smth(self):
        print('yeah')


class XmppBackendBackendTestCase(TestCase):
    pass
