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

from datetime import datetime

import requests

from xmpp_backends.base import XmppBackendBase  # NOQA
from xmpp_backends.base import BackendError  # NOQA
from xmpp_backends.base import UserExists  # NOQA

log = logging.getLogger(__name__)


class EjabberdRestBackend(XmppBackendBase):
    """This backend uses the Ejabberd XMLRPC interface.

    In addition to `mod_xmlrpc`, this backend requires `mod_admin_extra` to be installed.

    .. WARNING:: If you use ejabberd <= 14.07, please take special care of the `utf8_encoding`
        parameter.

    **ejabberd configuration:** The ``xmlrpc`` module is included with ejabberd_ since version
    13.12. If you use an earlier version, please get and run the module from the
    ``ejabberd-contrib`` repository. Configuring the interface is simple::

        listen:
            - ip: "127.0.0.1"
              port: 4560
              module: ejabberd_xmlrpc

    :param           uri: Directly passed to xmlrpclib, defaults to `http://127.0.0.1:4560`.
    :param     transport: Directly passed to xmlrpclib.
    :param      encoding: Directly passed to xmlrpclib.
    :param       verbose: Directly passed to xmlrpclib.
    :param    allow_none: Directly passed to xmlrpclib.
    :param  use_datetime: Directly passed to xmlrpclib.
    :param       context: Directly passed to xmlrpclib. Note that this parameter is ignored in
        in Python3. It's still documented but no longer accepted by the ServerProxy constructor.
    :param          user: Username of the JID used for authentication.
    :param        server: Server of the JID used for authenticiation.
    :param      password: The password of the given JID.
    :param utf8_encoding: How utf-8 characters are encoded. Valid values are `standard`, `php`,
        `python2` and `none`. Use `standard` for ejabberd > 14.07 and `php` for ejabberd <= 14.07.
        Please see comments in `xmpp_backends.xmlrpclib` if you care (don't!) about the details of
        this value. This parameter is ignored in Python3.
    """
    credentials = None

    def __init__(self, uri='http://127.0.0.1:5280/api/', **kwargs):
        super(EjabberdRestBackend, self).__init__()

        if not uri.endswith('/'):
            uri += '/'

        self.uri = uri
        self.kwargs = kwargs
        self.headers = kwargs.pop('headers', {})
        self.headers.setdefault('X-Admin', 'true')

    def post(self, cmd, allowed_status=None, **payload):
        if allowed_status is None:
            allowed_status = [200]

        uri = '%s%s' % (self.uri, cmd)
        response = requests.post(uri, json=payload, headers=self.headers, **self.kwargs)
        print('### HTTP %s: %s' % (response.status_code, response.content))

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
        result = response.json()['last_activity'].lower().strip()

        if result == 'never':
            return None
        elif result == 'online':
            return datetime.now()

        return datetime.strptime(result[:19], '%Y-%m-%d %H:%M:%S')

    def set_last_activity(self, username, domain, status, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())

        self.post('set_last', user=username, host=domain, timestamp=timestamp, status=status)

    def user_exists(self, username, domain):
        response = self.post('check_account', user=username, host=domain)
        if response.content == b'0':
            return True
        elif response.content == b'1':
            return False
        else:
            raise BackendError('Unknown Error')

    def check_password(self, username, domain, password):
        response = self.post('check_password', user=username, host=domain, password=password)
        if response.content == b'0':
            return True
        elif response.content == b'1':
            return False
        else:
            raise BackendError('Unknown Error')

    def set_password(self, username, domain, password):
        response = self.post('change_password', user=username, host=domain, newpass=password)
        if response.content == b'0':
            return True
        else:
            raise BackendError('Unknown Error')

    def has_usable_password(self, username, domain):
        return True

    def block_user(self, username, domain):
        self.post('ban_account', user=username, host=domain, reason='Blocked.')

    def set_email(self, username, domain, email):
        """Not yet implemented."""
        pass

    def check_email(self, username, domain, email):
        """Not yet implemented."""
        pass

    def message_user(self, username, domain, subject, message):
        """Currently use send_message_chat and discard subject, because headline messages are not
        stored by mod_offline."""

        kwargs = {
            'body': message,
            'from': domain,
            'subject': subject,
            'to': '%s@%s' % (username, domain),
            'type': 'normal',
        }
        self.post('send_message', **kwargs)

    def all_users(self, domain):
        return self.post('registered_users', host=domain).json()

    def remove_user(self, username, domain):
        response = self.post('unregister', user=username, host=domain)
        if response.content == b'""':
            return True
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
