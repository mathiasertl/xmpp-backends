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

from __future__ import unicode_literals

import ipaddress
import logging
import time
from datetime import datetime

import pytz
import six

from .base import BackendError
from .base import UserExists
from .base import UserNotFound
from .base import UserSession
from .base import XmppBackendBase
from .constants import CONNECTION_XMPP

log = logging.getLogger(__name__)


class DummyBackend(XmppBackendBase):
    """A dummy backend for development using Djangos caching framework.

    By default, Djangos caching framework uses in-memory data structures, so every registration will be
    removed if you restart the development server.  You can configure a different cache (e.g. memcached), see
    `Django's cache framework <https://docs.djangoproject.com/en/dev/topics/cache/>`_ for details.

    :params domains: A list of domains to serve.
    """

    library = 'django.core.cache.cache'

    def __init__(self, domains):
        super(DummyBackend, self).__init__()
        self._domains = domains

    def get_api_version(self):
        return (1, 0)

    def user_exists(self, username, domain):
        if domain not in self._domains:
            return False

        user = '%s@%s' % (username, domain)
        return self.module.get(user) is not None

    def user_sessions(self, username, domain):
        user = '%s@%s' % (username, domain)
        return self.module.get(user, {}).get('sessions', set())

    def start_user_session(self, username, domain, resource, **kwargs):
        """Method to add a user session for debugging.

        Accepted parameters are the same as to the constructor of :py:class:`~xmpp_backends.base.UserSession`.
        """

        kwargs.setdefault('uptime', pytz.utc.localize(datetime.utcnow()))
        kwargs.setdefault('priority', 0)
        kwargs.setdefault('status', 'online')
        kwargs.setdefault('status_text', '')
        kwargs.setdefault('connection_type', CONNECTION_XMPP)
        kwargs.setdefault('encrypted', True)
        kwargs.setdefault('compressed', False)
        kwargs.setdefault('ip_address', '127.0.0.1')
        if six.PY2 and isinstance(kwargs['ip_address'], str):
            # ipaddress constructor does not eat str in py2 :-/
            kwargs['ip_address'] = kwargs['ip_address'].decode('utf-8')
        if isinstance(kwargs['ip_address'], six.string_types):
            kwargs['ip_address'] = ipaddress.ip_address(kwargs['ip_address'])

        user = '%s@%s' % (username, domain)
        session = UserSession(self, username, domain, resource, **kwargs)

        data = self.module.get(user)
        if data is None:
            raise UserNotFound(username, domain, resource)

        data.setdefault('sessions', set())
        if isinstance(data['sessions'], list):
            # Cast old data to set
            data['sessions'] = set(data['sessions'])

        data['sessions'].add(session)
        self.module.set(user, data)

        all_sessions = self.module.get('all_sessions', set())
        all_sessions.add(session)
        self.module.set('all_sessions', all_sessions)

    def stop_user_session(self, username, domain, resource, reason=''):
        user = '%s@%s' % (username, domain)
        data = self.module.get(user)
        if data is None:
            raise UserNotFound(username, domain)

        data['sessions'] = set([d for d in data.get('sessions', []) if d.resource != resource])
        self.module.set(user, data)

        all_sessions = self.module.get('all_sessions', set())
        all_sessions = set([s for s in all_sessions if s.jid != user])
        self.module.set('all_sessions', all_sessions)

    def create_user(self, username, domain, password, email=None):
        if domain not in self._domains:
            raise BackendError('Backend does not serve domain %s.' % domain)
        user = '%s@%s' % (username, domain)
        log.debug('Create user: %s (%s)', user, password)

        data = self.module.get(user)
        if data is None:
            data = {
                'pass': password,
                'last_status': (time.time(), 'Registered'),
                'sessions': set(),
            }
            if email is not None:
                data['email'] = email
            self.module.set(user, data)

            # maintain list of users in cache
            users = self.module.get('all_users', set())
            users.add(user)
            self.module.set('all_users', users)
        else:
            raise UserExists()

    def check_password(self, username, domain, password):
        user = '%s@%s' % (username, domain)
        log.debug('Check pass: %s -> %s', user, password)

        data = self.module.get(user)
        if data is None:
            return False
        else:
            return data['pass'] == password

    def check_email(self, username, domain, email):
        user = '%s@%s' % (username, domain)
        log.debug('Check email: %s --> %s', user, email)

        data = self.module.get(user)
        if data is None:
            return False
        else:
            return data['email'] == email

    def set_password(self, username, domain, password):
        user = '%s@%s' % (username, domain)
        log.debug('Set pass: %s -> %s', user, password)

        data = self.module.get(user)
        if data is None:
            raise UserNotFound(username, domain)
        else:
            data['pass'] = password
            self.module.set(user, data)

    def set_email(self, username, domain, email):
        user = '%s@%s' % (username, domain)
        log.debug('Set email: %s --> %s', user, email)

        data = self.module.get(user)
        if data is None:
            raise UserNotFound(username, domain)
        else:
            data['email'] = email
            self.module.set(user, data)

    def get_last_activity(self, username, domain):
        user = '%s@%s' % (username, domain)

        data = self.module.get(user)
        if data is None:
            raise UserNotFound(username, domain)
        else:
            return datetime.utcfromtimestamp(data['last_status'][0])

    def set_last_activity(self, username, domain, status='', timestamp=None):
        user = '%s@%s' % (username, domain)
        if timestamp is None:
            timestamp = time.time()
        else:
            timestamp = self.datetime_to_timestamp(timestamp)

        data = self.module.get(user)
        if data is None:
            pass  # NOTE: real APIs provide no error either :-/
        else:
            data['last_status'] = (timestamp, status)
            self.module.set(user, data)

    def block_user(self, username, domain):
        # overwritten so we pass tests
        self.set_password(username, domain, self.get_random_password())

    def all_domains(self):
        """Just returns the domains passed to the constructor."""

        return list(self._domains)

    def all_users(self, domain):
        return set([u.split('@')[0] for u in self.module.get('all_users', set())
                    if u.endswith('@%s' % domain)])

    def all_user_sessions(self):
        return self.module.get('all_sessions', set())

    def remove_user(self, username, domain):
        user = '%s@%s' % (username, domain)
        log.debug('Remove: %s', user)

        users = self.module.get('all_users', set())
        users.remove(user)
        self.module.set('all_users', users)

        self.module.delete(user)

    def stats(self, stat, domain=None):
        """Always returns 0."""
        return 0

    def message_user(self, username, domain, subject, message):
        user = '%s@%s' % (username, domain)
        data = self.module.get(user)
        if data is None:
            return  # user does not exist

        data.setdefault('messages', [])
        data['messages'].append({
            'date': datetime.utcnow(),
            'message': message,
            'sender': domain,
            'subject': subject,
        })
        self.module.set(user, data)
