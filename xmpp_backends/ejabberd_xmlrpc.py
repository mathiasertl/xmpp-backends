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
import warnings
from datetime import datetime
from datetime import timedelta

import pytz
import six
from six.moves.http_client import BadStatusLine

from .base import BackendConnectionError
from .base import BackendError
from .base import EjabberdBackendBase
from .base import NotSupportedError
from .base import UserExists
from .base import UserNotFound
from .base import UserSession

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
    :param      version: Deprecated, no longer use this parameter.
    """
    credentials = None

    def __init__(self, uri='http://127.0.0.1:4560', transport=None, encoding=None, verbose=0, allow_none=0,
                 use_datetime=0, context=None, user=None, server=None, password=None, version=None,
                 **kwargs):
        super(EjabberdXMLRPCBackend, self).__init__(**kwargs)

        if version is not None:
            warnings.warn("The version parameter is deprecated.", DeprecationWarning)

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

    def rpc(self, cmd, **kwargs):
        """Generic helper function to call an RPC method."""

        func = getattr(self.client, cmd)
        try:
            if self.credentials is None:
                return func(kwargs)
            else:
                return func(self.credentials, kwargs)
        except socket.error as e:
            raise BackendConnectionError(e)
        except (xmlrpclib.ProtocolError, BadStatusLine) as e:
            log.error(e)
            raise BackendError("Error reaching backend.")

    def get_api_version(self):
        result = self.rpc('status')
        if result['res'] == 0:
            return self.parse_status_string(result.get('text', ''))
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

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

        if self.api_version < (17, 4):
            # ejabberd 17.04 introduced a change:
            #       https://github.com/processone/ejabberd/issues/1565
            activity = result['last_activity']
            if activity == 'Online':
                return datetime.utcnow()
            elif activity == 'Never':
                if self.user_exists(username, domain):
                    return None
                raise UserNotFound(username, domain)
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
        sessions = set()
        for data in raw_sessions:
            # The data structure is a bit weird, its a list of one-element dicts.  We itemize each dict and
            # then flatten the resulting list
            session = [d.items() for d in data['session']]
            session = dict([item for sublist in session for item in sublist])

            started = pytz.utc.localize(datetime.utcnow() - timedelta(seconds=session['uptime']))
            typ, encrypted, compressed = self.parse_connection_string(session['connection'])
            sessions.add(UserSession(
                backend=self,
                username=username,
                domain=domain,
                resource=session['resource'],
                priority=session['priority'],
                ip_address=self.parse_ip_address(session['ip']),
                uptime=started,
                status=session['status'],
                status_text=session['statustext'],
                connection_type=typ, encrypted=encrypted, compressed=compressed
            ))
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
        if self.api_version <= (16, 1, ) and not self.user_exists(username, domain):
            # 16.01 just creates the user upon change_password!
            # NOTE: This may also affect other versions < 16.09.
            raise UserNotFound(username, domain)

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
        try:
            result = self.rpc('ban_account', user=username, host=domain, reason='Blocked.')
        except BackendError:
            if self.api_version == (14, 7):
                raise NotSupportedError('ejabberd 14.07 does not support getting all sessions via xmlrpc.')
            raise

        if result['res'] == 0:
            return
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def message_user(self, username, domain, subject, message):
        """Currently use send_message_chat and discard subject, because headline messages are not
        stored by mod_offline."""

        kwargs = {
            'body': message,
            'from': domain,
            'to': '%s@%s' % (username, domain),
        }

        if self.api_version <= (14, 7):
            # TODO: it's unclear when send_message was introduced
            command = 'send_message_chat'
        else:
            command = 'send_message'
            kwargs['subject'] = subject
            kwargs['type'] = 'normal'
        result = self.rpc(command, **kwargs)

        if result['res'] == 0:
            return
        else:
            raise BackendError(result.get('text', 'Unknown Error'))

    def all_domains(self):
        return [d['vhost'] for d in self.rpc('registered_vhosts')['vhosts']]

    def all_users(self, domain):
        users = self.rpc('registered_users', host=domain)['users']
        return set([e['username'] for e in users])

    def all_user_sessions(self):
        try:
            result = self.rpc('connected_users_info')['connected_users_info']
        except BackendError:
            if self.api_version == (14, 7):
                raise NotSupportedError('ejabberd 14.07 does not support getting all sessions via xmlrpc.')
            raise

        if self.api_version < (18, 6):
            # The key used here was silently changed in 18.06.
            sessions_key = 'sessions'
        else:
            sessions_key = 'session'

        sessions = set()
        for data in result:
            # The data structure is a bit weird, its a list of one-element dicts.  We itemize each dict and
            # then flatten the resulting list
            session = [d.items() for d in data[sessions_key]]
            session = dict([item for sublist in session for item in sublist])

            username, domain = session['jid'].split('@', 1)
            domain, resource = domain.split('/', 1)
            started = pytz.utc.localize(datetime.utcnow() - timedelta(seconds=session['uptime']))
            typ, encrypted, compressed = self.parse_connection_string(session['connection'])
            sessions.add(UserSession(
                backend=self,
                username=username,
                domain=domain,
                resource=resource,
                priority=session['priority'],
                ip_address=self.parse_ip_address(session['ip']),
                uptime=started,
                status=session.get('status', ''),  # ejabberd <= 18.04 does not contain this key
                status_text=session.get('statustext', ''),  # ejabberd <= 18.04 does not contain this key
                connection_type=typ, encrypted=encrypted, compressed=compressed
            ))
        return sessions

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
