# -*- coding: utf-8 -*-
#
# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends.  If not, see
# <http://www.gnu.org/licenses/>.

import ipaddress

import pytz
from django.conf import settings
from django.utils import timezone

from ...base import UserNotFound
from ...base import UserSession
from ...base import XmppBackendBase
from ...constants import CONNECTION_XMPP
from .models import FakeUser
from .models import FakeUserSession


class FakeXMPPBackend(XmppBackendBase):
    """A backend that uses the ``xmpp_backends.django.fake_xmpp`` Django app as backend.

    This backend is useful if you develop a Django application and don't want to run a real XMPP server.

    .. WARNING:: This backend is not intended for production use.

    :param domains: A list of domains this backend should serve.
    """

    def __init__(self, domains):
        super(FakeXMPPBackend, self).__init__()
        self._domains = domains

    def get_api_version(self):
        return (1, 0)

    def all_domains(self):
        return list(self._domains)

    def all_user_sessions(self):
        return set([UserSession(
            backend=self,
            username=s.user.node,
            domain=s.user.domain,
            resource=s.resource,
            priority=s.priority,
            ip_address=ipaddress.ip_address(s.ip_address),
            uptime=s.uptime,
            status=s.status,
            status_text=s.status_text,
            connection_type=s.connection_type,
            encrypted=s.encrypted,
            compressed=s.compressed
        ) for s in FakeUserSession.objects.all()])

    def all_users(self, domain):
        qs = FakeUser.objects.filter(username__endswith='@%s' % domain)
        return set([u.split('@', 1)[0] for u in qs.values_list('username', flat=True)])

    def block_user(self, username, domain):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)
        user.is_blocked = True
        user.set_password(None)  # sets an unuseable password
        user.save()

    def check_email(self, username, domain, email):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        return user.email == email

    def check_password(self, username, domain, password):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            return False

        return user.check_password(password)

    def create_user(self, username, domain, password, email=None):
        user = FakeUser.objects.create(username='%s@%s' % (username, domain), email=email)
        user.set_password(password)
        user.save()

    def get_last_activity(self, username, domain):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)
        if timezone.is_aware(user.last_activity):
            return timezone.make_naive(user.last_activity)
        else:
            return user.last_activity

    def message_user(self, username, domain, subject, message):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            return  # ejabberd does not return anything either

        user.message(subject, message, sender=domain)

    def remove_user(self, username, domain):
        FakeUser.objects.filter(username='%s@%s' % (username, domain)).delete()

    def set_email(self, username, domain, email):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        user.email = email
        user.save()

    def set_last_activity(self, username, domain, status=u'', timestamp=None):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            return

        if timestamp is None:
            timestamp = timezone.now()
        elif settings.USE_TZ and timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp, pytz.utc)
        elif not settings.USE_TZ and timezone.is_aware(timestamp):
            timestamp = timezone.make_naive(timestamp, pytz.utc)

        user.last_activity = timestamp
        user.save()

    def set_password(self, username, domain, password):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        user.set_password(password)
        user.save()

    def start_user_session(self, username, domain, resource, **kwargs):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        kwargs.setdefault('uptime', timezone.now())
        kwargs.setdefault('priority', 0)
        kwargs.setdefault('status', 'online')
        kwargs.setdefault('status_text', '')
        kwargs.setdefault('connection_type', CONNECTION_XMPP)
        kwargs.setdefault('encrypted', True)
        kwargs.setdefault('compressed', False)
        kwargs.setdefault('ip_address', '127.0.0.1')

        FakeUserSession.objects.create(user=user, resource=resource, **kwargs)

    def stats(self, stat, domain=None):
        if stat == 'registered_users':
            qs = FakeUser.objects.all()
            if domain:
                qs = qs.filter(username__endswith='@%s' % domain)
            return qs.count()

        elif stat == 'online_users':
            qs = FakeUserSession.objects.all()
            if domain:
                qs = qs.filter(user__username__endswith='@%s' % domain)

            return len(set([s.user_id for s in qs]))

    def stop_user_session(self, username, domain, resource, reason=''):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        FakeUserSession.objects.filter(user=user, resource=resource).delete()

    def user_exists(self, username, domain):
        return FakeUser.objects.filter(username='%s@%s' % (username, domain)).exists()

    def user_sessions(self, username, domain):
        try:
            user = FakeUser.objects.get(username='%s@%s' % (username, domain))
        except FakeUser.DoesNotExist:
            raise UserNotFound(username, domain)

        return set([UserSession(
            backend=self,
            username=s.user.node,
            domain=s.user.domain,
            resource=s.resource,
            priority=s.priority,
            ip_address=ipaddress.ip_address(s.ip_address),
            uptime=s.uptime,
            status=s.status,
            status_text=s.status_text,
            connection_type=s.connection_type,
            encrypted=s.encrypted,
            compressed=s.compressed
        ) for s in user.sessions.all()])
