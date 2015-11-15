# -*- coding: utf-8 -*-
#

import inspect
import unittest

from xmpp_backends.base import XmppBackendBase
from xmpp_backends.ejabberd_xmlrpc import EjabberdXMLRPCBackend


class TestInterfaces(unittest.TestCase):
    def assertEqualInterface(self, subclass):
        for name, base_func in inspect.getmembers(XmppBackendBase, callable):
            if name.startswith('_'):
                continue

            self.assertEqual(
                inspect.getargspec(base_func),
                inspect.getargspec(getattr(subclass, name)),
                "%s.%s has a different signature" % (subclass.__name__, name)
            )

    def test_ejabberd_xmlrpc(self):
        self.assertEqualInterface(EjabberdXMLRPCBackend)
