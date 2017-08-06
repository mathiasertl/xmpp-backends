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

import logging
import time
from datetime import datetime

from .base import UserExists
from .base import UserNotFound
from .base import XmppBackendBase

log = logging.getLogger(__name__)


class DummyBackend(XmppBackendBase):
    """A dummy backend for development using Djangos caching framework.

    By default, Djangos caching framework uses in-memory data structures, so every registration will be
    removed if you restart the development server.  You can configure a different cache (e.g. memcached), see
    `Django's cache framework <https://docs.djangoproject.com/en/dev/topics/cache/>`_ for details.
    """

    library = 'django.core.cache.cache'

    def user_exists(self, username, domain):
        user = '%s@%s' % (username, domain)
        return self.module.get(user) is not None

    def user_sessions(self, username, domain):
        user = '%s@%s' % (username, domain)
        return self.module.get(user).get('sessions', [])

    def start_user_session(self, username, domain, resource, ip='127.0.0.1', priority=0,
                           started=None, status='available', statustext=''):
        """Method to add a user session for debugging.

        :param   username: The username of the user.
        :type    username: str
        :param     domain: The domain of the user.
        :type      domain: str
        :param   resource: The resource for the connection. This identifies the session.
        :param         ip: The IP the user connects from, defaults to ``"127.0.0.1"``.
        :type          ip: str
        :param   priority: The priority of the connection, defaults to ``0``.
        :type    priority: int
        :param    started: When the connection was started, defaults to "now".
        :type     started: datetime
        :param     status: The status used, defaults to ``"available"``.
        :param statustext: The status text, defaults to ``""``.
        """

        if started is None:
            started = datetime.utcnow()

        user = '%s@%s' % (username, domain)
        data = self.module.get(user)
        data.setdefault('sessions', [])

        data['sessions'].append({
            'ip': ip,
            'priority': priority,
            'started': started,
            'status': status,
            'resource': resource,
            'statustext': statustext,
        })
        self.module.set(user, data)

    def stop_user_session(self, username, domain, resource, reason=''):
        user = '%s@%s' % (username, domain)
        data = self.module.get(user)
        data['sessions'] = [d for d in data.get('sessions', []) if d['resource'] != resource]
        self.module.set(user, data)

    def create_user(self, username, domain, password, email=None):
        user = '%s@%s' % (username, domain)
        log.debug('Create user: %s (%s)', user, password)

        data = self.module.get(user)
        if data is None:
            data = {
                'pass': password,
                'last_status': (time.time(), 'Registered'),
                'sessions': [],
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

    def all_users(self, domain):
        return set([u.split('@')[0] for u in self.module.get('all_users', set())
                    if u.endswith('@%s' % domain)])

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
