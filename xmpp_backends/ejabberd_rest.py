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

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from datetime import datetime
from datetime import timedelta

import requests

from .base import BackendError
from .base import EjabberdBackendBase
from .base import UserExists
from .base import UserNotFound

log = logging.getLogger(__name__)


class EjabberdRestBackend(EjabberdBackendBase):
    """This backend uses the Ejabberd REST interface.

    The module implements ejabberds still somewhat sparsely documented `REST API
    <https://docs.ejabberd.im/developer/ejabberd-api/>`_. It requires `requests
    <http://docs.python-requests.org/en/master/>`_.

    Our current (17.07) configuration looks as follows::

        # "api" is an access_rules list
        commands_admin_access: api
        commands:
          - add_commands:
            - change_password
            # ... other commands, see:
            # http://xmpp-backends.readthedocs.io/en/latest/xmpp_backends/backends.html#required-commands

        listen:
          # other ports here...
          - ip: "127.0.0.1"
            port: 5280
            module: ejabberd_http
            request_handlers:
              "/oauth": ejabberd_oauth
              "/api": mod_http_api

            # Requires ejabberd 17.04 or later, otherwise you should pass a version in the
            # constructor.
            custom_headers:
              "Ejabberd-Version": "@VERSION@"

            # Please use TLS if you're not on localhost! Help:
            #  http://xmpp-backends.readthedocs.io/en/latest/xmpp_backends/backends.html#ejabberd-tls-setup
            #tls: true
            #...

    :param       uri: The URI of the API.
    :param      user: User used in authenticating with the API.
    :param  password: Password used in authenticating with the API.
    :param   version: A tuple describing the version used, e.g. ``(16, 12,)``. See
        :ref:`version parameter <ejabberd_version>` for a more detailed explanation.
    :param \**kwargs: All keyword parameters are directly passed to the ``requests`` module. Please
        see the documentation there for possible parameters (e.g. SSL validation, etc.).
    """
    credentials = None

    def __init__(self, uri='http://127.0.0.1:5280/api/', user=None, password=None,
                 version=(17, 7, ), **kwargs):
        super(EjabberdRestBackend, self).__init__()

        if not uri.endswith('/'):
            uri += '/'

        self.uri = uri
        self.kwargs = kwargs
        self.headers = kwargs.pop('headers', {})
        self.headers.setdefault('X-Admin', 'true')
        self.version = version
        if user:
            self.kwargs['auth'] = (user, password)

    def get_version(self, response):
        if response.headers.get('Ejabberd-Version'):
            return response.headers.get('Ejabberd-Version').split('.')
        return self.version

    def post(self, cmd, allowed_status=None, **payload):
        if allowed_status is None:
            allowed_status = [200]

        uri = '%s%s' % (self.uri, cmd)
        response = requests.post(uri, json=payload, headers=self.headers, **self.kwargs)

        if response.status_code not in allowed_status:
            raise BackendError('HTTP %s: %s' % (response.status_code, response.content))
        return response

    def create_user(self, username, domain, password, email=None):
        result = self.post('register', user=username, host=domain, password=password,
                           allowed_status=[200, 409])

        if result.status_code == 200:
            try:
                # we ignore errors here because not setting last activity is only a problem in
                # edge-cases.
                self.set_last_activity(username, domain, status='Registered')
            except BackendError as e:
                log.error('Error setting last activity: %s', e)

            if email is not None:
                self.set_email(username, domain, email)
        elif result.status_code == 409:
            raise UserExists()
        else:
            # NOTE: This really should never happen, only 200 and 409 don't raise an exception.
            raise BackendError(result.get('text', 'Unknown Error'))

    def get_last_activity(self, username, domain):
        response = self.post('get_last', user=username, host=domain)
        version = self.get_version(response)

        if version < (17, 4):
            result = response.json()['last_activity'].lower().strip()

            if result == 'never':
                return None
            elif result == 'online':
                return datetime.now()

            return datetime.strptime(result[:19], '%Y-%m-%d %H:%M:%S')

        # ejabberd 17.04 introduced a change:
        #       https://github.com/processone/ejabberd/issues/1565
        else:
            parsed = response.json()
            if parsed['status'] == 'NOT FOUND':
                raise UserNotFound(username, domain)

            timestamp = parsed['timestamp']
            if len(timestamp) == 27:
                # NOTE: This format is encountered when the user is not found.
                fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            else:
                fmt = '%Y-%m-%dT%H:%M:%SZ'

            return datetime.strptime(parsed['timestamp'], fmt)

    def set_last_activity(self, username, domain, status='', timestamp=None):
        timestamp = self.datetime_to_timestamp(timestamp)
        self.post('set_last', user=username, host=domain, timestamp=timestamp, status=status)

    def user_exists(self, username, domain):
        response = self.post('check_account', user=username, host=domain)
        if response.content == b'0':
            return True
        elif response.content == b'1':
            return False
        else:
            raise BackendError('Unknown Error')

    def user_sessions(self, username, domain):
        response = self.post('user_sessions_info', user=username, host=domain)
        data = response.json()
        sessions = []
        for d in data:
            started = datetime.utcnow() - timedelta(seconds=d['uptime'])
            ip = d['ip']
            if ip.startswith('::FFFF:'):
                ip = ip[7:]

            sessions.append({
                'ip': ip,
                'priority': d['priority'],
                'started': started,
                'status': d['status'],
                'resource': d['resource'],
                'statustext': d['statustext'],
            })
        return sessions

    def stop_user_session(self, username, domain, resource, reason=''):
        response = self.post('kick_session', user=username, host=domain, resource=resource,
                             reason=reason)
        return response

    def check_password(self, username, domain, password):
        response = self.post('check_password', user=username, host=domain, password=password)
        if response.content == b'0':
            return True
        elif response.content == b'1':
            return False
        else:
            raise BackendError('Unknown Error')

    def set_password(self, username, domain, password):
        response = self.post('change_password', user=username, host=domain, newpass=password,
                             allowed_status=[200, 404])
        if response.content == b'0':
            return
        elif response.status_code == 404:
            raise UserNotFound(username, domain)
        else:
            raise BackendError('Unknown Error')

    def block_user(self, username, domain):
        self.post('ban_account', user=username, host=domain, reason='Blocked.')

    def message_user(self, username, domain, subject, message):
        kwargs = {
            'body': message,
            'from': domain,
            'subject': subject,
            'to': '%s@%s' % (username, domain),
            'type': 'normal',
        }
        self.post('send_message', **kwargs)

    def all_users(self, domain):
        return set(self.post('registered_users', host=domain).json())

    def remove_user(self, username, domain):
        response = self.post('unregister', user=username, host=domain)
        if response.content == b'""':
            return
        else:
            raise BackendError('Unknown Error')

    def stats(self, stat, domain=None):
        if stat == 'registered_users':
            stat = 'registeredusers'
        elif stat == 'online_users':
            stat = 'onlineusers'
        else:
            raise ValueError("Unknown stat %s" % stat)

        if domain is None:
            result = self.post('stats', name=stat).json()
        else:
            result = self.post('stats_host', name=stat, host=domain).json()

        try:
            return result['stat']
        except KeyError:
            raise BackendError(result.get('text', 'Unknown Error'))
