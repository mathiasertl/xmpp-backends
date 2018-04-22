# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FakeXmppConfig(AppConfig):
    name = 'xmpp_backends.django.fake_xmpp'
    verbose_name = _('Fake XMPP server')
