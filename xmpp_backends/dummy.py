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

from __future__ import unicode_literals

import logging
import time

from .base import XmppBackendBase
from .base import UserExists
from .base import UserNotFound

log = logging.getLogger(__name__)


class DummyBackend(XmppBackendBase):
    """A dummy backend for development using Djangos caching framework.

    By default, Djangos caching framework uses in-memory data structures, so
    every registration will be removed if you restart the development server.
    You can configure a different cache (e.g. memcached), see
    `Django's cache framework <https://docs.djangoproject.com/en/dev/topics/cache/>`_
    for details.
    """

    library = 'django.core.cache'

    def user_exists(self, username, domain):
        user = '%s@%s' % (username, domain)
        return self.module.get(user) is not None

    def create_user(self, username, domain, password, email=None):
        user = '%s@%s' % (username, domain)
        log.debug('Create user: %s (%s)', user, password)

        data = self.module.get(user)
        if data is None:
            data = {
                'pass': password,
                'last_status': (time.time(), 'Registered'),
            }
            if email is not None:
                data['email'] = email
            self.module.set(user, data)
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
            raise UserNotFound("User does not exist in backend.")
        else:
            data['pass'] = password
            self.module.set(user, data)

    def set_email(self, username, domain, email):
        user = '%s@%s' % (username, domain)
        log.debug('Set email: %s --> %s', user, email)

        data = self.module.get(user)
        if data is None:
            raise UserNotFound()
        else:
            data['email'] = email
            self.module.set(user, data)

    def set_last_activity(self, username, domain, status, timestamp=None):
        user = '%s@%s' % (username, domain)
        if timestamp is None:
            timestamp = time.time()

        data = self.module.get(user)
        if data is None:
            raise UserNotFound()
        else:
            data['last_status'] = (time.time(), status)
            self.module.set(user, data)

    def all_users(self, domain):
        return set()

    def remove_user(self, username, domain):
        user = '%s@%s' % (username, domain)
        log.debug('Remove: %s', user)

        self.module.delete(user)
