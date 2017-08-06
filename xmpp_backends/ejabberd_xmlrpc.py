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
import socket
from datetime import datetime
from datetime import timedelta

import six

from six.moves.http_client import BadStatusLine

from .base import BackendError
from .base import EjabberdBackendBase
from .base import UserExists
from .base import UserNotFound

if six.PY2:  # we have a special version for Python2
    from . import xmlrpclib
else:  # use the default for Python3 (god save us all!)
    from xmlrpc import client as xmlrpclib


log = logging.getLogger(__name__)


class EjabberdXMLRPCBackend(EjabberdBackendBase):
    """This backend uses the Ejabberd XMLRPC interface.

    In addition to an XMLRPC endpoint, this backend requires ``mod_admin_extra`` to be installed.

    .. WARNING::

        The backend does not handle UTF-8 characters correctly if you use ejabberd <= 14.07 and
        Python 3.

    **ejabberd configuration:** The ``xmlrpc`` module is included with ejabberd_ since version 13.12. If you
    use an earlier version, please get and run the module from the `ejabberd-contrib
    <https://github.com/processone/ejabberd-contrib>`_ repository. Configuring the interface is simple::

        listen:
            - ip: "127.0.0.1"
              port: 4560
              module: ejabberd_xmlrpc

    :param          uri: Directly passed to xmlrpclib, defaults to ``"http://127.0.0.1:4560"``.
    :param    transport: Directly passed to xmlrpclib.
    :param     encoding: Directly passed to xmlrpclib.
    :param      verbose: Directly passed to xmlrpclib.
    :param   allow_none: Directly passed to xmlrpclib.
    :param use_datetime: Directly passed to xmlrpclib.
    :param      context: Directly passed to xmlrpclib. Ignored in in Python3, where the parameter is still
        documented but no longer accepted by the ServerProxy constructor.
    :param         user: Username of the JID used for authentication.
    :param       server: Server of the JID used for authenticiation.
    :param     password: The password of the given JID.
    :param      version: A tuple describing the ejabberd version used, e.g. ``(16, 12,)``. See
        :ref:`version parameter <ejabberd_version>` for a more detailed explanation.
    """
    credentials = None

    def __init__(self, uri='http://127.0.0.1:4560', transport=None, encoding=None, verbose=0, allow_none=0,
                 use_datetime=0, context=None, user=None, server=None, password=None, version=(17, 7, )):
        super(EjabberdXMLRPCBackend, self).__init__()

        kwargs = {
            'transport': transport,
            'encoding': encoding,
            'verbose': verbose,
            'allow_none': allow_none,
            'use_datetime': use_datetime,
        }
        if six.PY2 and version <= (14, 7, ):
            kwargs['utf8_encoding'] = 'php'
            kwargs['context'] = context

        self.client = xmlrpclib.ServerProxy(uri, **kwargs)
        if user is not None:
            self.credentials = {
                'user': user,
                'server': server,
                'password': password,
            }
        self.version = version

    def get_version(self):
        return self.version

    def rpc(self, cmd, **kwargs):
        """Generic helper function to call an RPC method."""

        func = getattr(self.client, cmd)
        try:
            if self.credentials is None:
                return func(kwargs)
            else:
                return func(self.credentials, kwargs)
        except (xmlrpclib.ProtocolError, BadStatusLine, socket.error) as e:
            log.error(e)
            raise BackendError("Error reaching backend.")

    def create_user(self, username, domain, password, email=None):
        result = self.rpc('register', user=username, host=domain, password=password)

        if result['res'] == 0:
            try:
                # we ignore errors here because not setting last activity is only a problem in edge-cases.
                self.set_last_activity(username, domain, status='Registered')
            except BackendError as e:
                log.error('Error setting last activity: %s', e)

            if email is not None:
                self.set_email(username, domain, email)
        elif result['res'] == 1:
            raise UserExists()
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def get_last_activity(self, username, domain):
        result = self.rpc('get_last', user=username, host=domain)
        version = self.get_version()

        if version < (17, 4):
            # ejabberd 17.04 introduced a change:
            #       https://github.com/processone/ejabberd/issues/1565
            activity = result['last_activity']
            if activity == 'Online':
                return datetime.utcnow()
            elif activity == 'Never':
                return None
            else:
                return datetime.strptime(activity[:19], '%Y-%m-%d %H:%M:%S')
        else:
            data = result['last_activity']
            if data[1]['status'] == 'NOT FOUND':
                raise UserNotFound(username, domain)

            timestamp = data[0]['timestamp']
            if len(timestamp) == 27:
                # NOTE: This format is encountered when the user is not found.
                fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            else:
                fmt = '%Y-%m-%dT%H:%M:%SZ'

            return datetime.strptime(timestamp, fmt)

    def set_last_activity(self, username, domain, status='', timestamp=None):
        timestamp = self.datetime_to_timestamp(timestamp)
        self.rpc('set_last', user=username, host=domain, timestamp=timestamp, status=status)

    def user_exists(self, username, domain):
        result = self.rpc('check_account', user=username, host=domain)
        if result['res'] == 0:
            return True
        elif result['res'] == 1:
            return False
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def user_sessions(self, username, domain):
        result = self.rpc('user_sessions_info', user=username, host=domain)
        raw_sessions = result.get('sessions_info', [])
        sessions = []
        for data in raw_sessions:
            # The data structure is a bit weird, its a list of one-element dicts.  We itemize each dict and
            # then flatten the resulting list
            session = [d.items() for d in data['session']]
            session = dict([item for sublist in session for item in sublist])

            started = datetime.utcnow() - timedelta(seconds=session['uptime'])
            ip = session['ip']
            if ip.startswith('::FFFF:'):
                ip = ip[7:]

            sessions.append({
                'ip': ip,
                'priority': session['priority'],
                'started': started,
                'status': session['status'],
                'resource': session['resource'],
                'statustext': session['statustext'],
            })
        return sessions

    def stop_user_session(self, username, domain, resource, reason=''):
        result = self.rpc('kick_session', user=username, host=domain, resource=resource,
                          reason=reason)
        return result

    def check_password(self, username, domain, password):
        result = self.rpc('check_password', user=username, host=domain, password=password)
        if result['res'] == 0:
            return True
        elif result['res'] == 1:
            return False
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def set_password(self, username, domain, password):
        try:
            result = self.rpc('change_password', user=username, host=domain, newpass=password)
        except xmlrpclib.Fault as e:
            if e.faultCode == -118:
                raise UserNotFound(username, domain)
            raise BackendError('Unknown Error')

        if result['res'] == 0:
            return
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def block_user(self, username, domain):
        self.rpc('ban_account', user=username, host=domain, reason='Blocked.')

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
        self.rpc('send_message', **kwargs)

    def all_users(self, domain):
        users = self.rpc('registered_users', host=domain)['users']
        return set([e['username'] for e in users])

    def remove_user(self, username, domain):
        result = self.rpc('unregister', user=username, host=domain)
        if result['res'] == 0:
            return
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def stats(self, stat, domain=None):
        if stat == 'registered_users':
            stat = 'registeredusers'
        elif stat == 'online_users':
            stat = 'onlineusers'
        else:
            raise ValueError("Unknown stat %s" % stat)

        if domain is None:
            result = self.rpc('stats', name=stat)
        else:
            result = self.rpc('stats_host', name=stat, host=domain)

        try:
            return result['stat']
        except KeyError:
            raise BackendError(result.get('text', 'Unknown Error'))
