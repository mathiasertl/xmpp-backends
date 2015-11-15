# -*- coding: utf-8 -*-
#


import unittest
import xmlrpclib as stdxmlrpclib

from xmpp_backends import xmlrpclib


class TestUnicodeChars(unittest.TestCase):
    def parse_response(self, resp):
        return resp[32:resp.find('</string>')]

    def get_response(self, marshaller, data):
        """Marshal the response and strip XML.

        This purposly does not use any XML parsing to strip the XML from the marshalled data so
        that no XML parsing is involved that might change the data."""
        resp = marshaller.dumps([data])
        return self.parse_response(resp)

    def test_get_response(self):
        # test parsing the response too:
        tmpl = '<params>\n<param>\n<value><string>%s</string></value>\n</param>\n</params>\n'

        self.assertEqual(self.parse_response(tmpl % ''), '')
        self.assertEqual(self.parse_response(tmpl % 'a'), 'a')
        self.assertEqual(self.parse_response(tmpl % 'abc'), 'abc')
        self.assertEqual(self.parse_response(tmpl % '&#532;'), '&#532;')

    def test_standard(self):
        m = xmlrpclib.Marshaller()

        self.assertEqual(self.get_response(m, 'ä'), '&#228;')
        self.assertEqual(self.get_response(m, u'ä'), '&#228;')
        self.assertEqual(self.get_response(m, 'aäb'), 'a&#228;b')
        self.assertEqual(self.get_response(m, u'aäb'), 'a&#228;b')
        self.assertEqual(self.get_response(m, u'&ä<>'), '&amp;&#228;&lt;&gt;')
        self.assertEqual(self.get_response(m, '&ä<>'), '&amp;&#228;&lt;&gt;')

    def test_php(self):
        m = xmlrpclib.Marshaller(utf8_encoding='php')

        self.assertEqual(self.get_response(m, 'ä'), '&#195;&#164;')
        self.assertEqual(self.get_response(m, u'ä'), '&#195;&#164;')
        self.assertEqual(self.get_response(m, 'aäb'), 'a&#195;&#164;b')
        self.assertEqual(self.get_response(m, u'aäb'), 'a&#195;&#164;b')
        self.assertEqual(self.get_response(m, u'&ä<>'), '&amp;&#195;&#164;&lt;&gt;')
        self.assertEqual(self.get_response(m, '&ä<>'), '&amp;&#195;&#164;&lt;&gt;')

    def assertXmlRpcEqual(self, value):
        m1 = xmlrpclib.Marshaller(utf8_encoding='python2')
        m2 = stdxmlrpclib.Marshaller()

        value1 = m1.dumps(value)
        value2 = m2.dumps(value)
        self.assertEqual(value1, value2)

    def test_python2(self):
        self.assertXmlRpcEqual('ä')
        self.assertXmlRpcEqual('aäb')
        self.assertXmlRpcEqual('&ä<>')

        # py2 xmlrpclib does not accept unicode strs (except for empty unicode)
        with self.assertRaises(TypeError):
            self.assertXmlRpcEqual(u'a')
