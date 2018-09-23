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

import inspect
import unittest

import six

from xmpp_backends.base import XmppBackendBase
from xmpp_backends.django.fake_xmpp.backend import FakeXMPPBackend
from xmpp_backends.dummy import DummyBackend
from xmpp_backends.ejabberd_rest import EjabberdRestBackend
from xmpp_backends.ejabberd_xmlrpc import EjabberdXMLRPCBackend
from xmpp_backends.ejabberdctl import EjabberdctlBackend


class TestInterfaces(unittest.TestCase):
    def assertEqualInterface(self, subclass):
        for name, base_func in inspect.getmembers(XmppBackendBase, callable):
            if name.startswith('_'):
                continue

            if six.PY2:
                self.assertEqual(
                    inspect.getargspec(base_func),
                    inspect.getargspec(getattr(subclass, name)),
                    "%s.%s has a different signature" % (subclass.__name__, name)
                )
            else:
                self.assertEqual(
                    inspect.signature(base_func),
                    inspect.signature(getattr(subclass, name)),
                    "%s.%s has a different signature" % (subclass.__name__, name)
                )

    def test_ejabberd_xmlrpc(self):
        self.assertEqualInterface(EjabberdXMLRPCBackend)

    def test_ejabberdctl(self):
        self.assertEqualInterface(EjabberdctlBackend)

    def test_ejabberd_rest(self):
        self.assertEqualInterface(EjabberdRestBackend)

    def test_dummy(self):
        self.assertEqualInterface(DummyBackend)

    def test_fake(self):
        self.assertEqualInterface(FakeXMPPBackend)


class TestImplemented(unittest.TestCase):
    allow_base_function = [
        'confirm_reservation',
        'create_reservation',
        'datetime_to_timestamp',
        'expire_reservation',
        'get_random_password',
    ]

    def assertOverwritten(self, subclass):
        for name, base_func in inspect.getmembers(XmppBackendBase, callable):
            if name.startswith('_') or name in self.allow_base_function:
                continue

            self.assertNotEqual(getattr(XmppBackendBase, name),
                                getattr(subclass, name),
                                "%s.%s: Function is not overwritten." % (subclass.__name__, name))

    def test_ejabberd_rest(self):
        self.assertOverwritten(EjabberdRestBackend)

    def test_ejabberd_xmlrpc(self):
        self.assertOverwritten(EjabberdXMLRPCBackend)

    def test_ejabberdctl(self):
        self.assertOverwritten(EjabberdctlBackend)

    def test_dummy(self):
        self.assertOverwritten(DummyBackend)

    def test_fake(self):
        self.assertOverwritten(FakeXMPPBackend)
