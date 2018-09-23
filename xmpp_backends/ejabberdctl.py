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
import warnings
from datetime import datetime
from datetime import timedelta
from subprocess import PIPE
from subprocess import Popen

import pytz
import six

from .base import BackendError
from .base import EjabberdBackendBase
from .base import NotSupportedError
from .base import UserExists
from .base import UserNotFound
from .base import UserSession

log = logging.getLogger(__name__)


class EjabberdctlBackend(EjabberdBackendBase):
    """This backend uses the ejabberdctl command line utility.

    This backend requires ejabberds ``mod_admin_extra`` to be installed.

    .. WARNING::

       This backend is not very secure because ejabberdctl gets any passwords in clear text via the
       commandline. The process list (and thus the passwords) can usually be viewed by anyone that has
       shell-access to your machine!

    :param    path: Optional path to the ``ejabberdctl`` script. The default is ``"/usr/sbin/ejabberdctl"``.
                    The path can also be a list, e.g. if ejabberd is run inside a Docker image, you could set
                    ``['docker', 'exec', 'ejabberd-container', '/usr/sbin/ejabberdctl']``.
    :param version: Deprecated, no longer use this parameter.
    """

    def __init__(self, path='/usr/sbin/ejabberdctl', version=None, **kwargs):
        super(EjabberdctlBackend, self).__init__(**kwargs)

        if version is not None:
            warnings.warn("The version parameter is deprecated.", DeprecationWarning)

        self.ejabberdctl = path
        if isinstance(path, six.string_types):
            self.ejabberdctl = [path]

        if self.api_version <= (14, 7):
            log.warn('ejabberd <= 14.07 is really broken and many calls will not work!')

    def ctl(self, *args):
        cmd = self.ejabberdctl + list(args)

        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

    def get_api_version(self):
        code, out, err = self.ctl('status')
        if code == 0:
            return self.parse_status_string(out.decode('utf-8'))
        else:
            raise BackendError(code)

    def user_exists(self, username, domain):
        code, out, err = self.ctl('check_account', username, domain)
        if code == 0:
            return True
        elif code == 1:
            return False
        else:
            raise BackendError(code)  # TODO: 3 means nodedown.

    def user_sessions(self, username, domain):
        code, out, err = self.ctl('user_sessions_info', username, domain)
        sessions = set()
        out = out.decode('utf-8')  # bytes -> str in py3, str -> unicode in py2

        for line in out.splitlines():
            conn, ip, _p, prio, _n, uptime, status, resource, status_text = line.split('\t', 8)
            started = pytz.utc.localize(datetime.utcnow() - timedelta(int(uptime)))

            if prio == 'undefined':
                prio = None
            else:
                prio = int(prio)

            typ, encrypted, compressed = self.parse_connection_string(conn)
            sessions.add(UserSession(
                backend=self,
                username=username,
                domain=domain,
                resource=resource,
                priority=prio,
                ip_address=self.parse_ip_address(ip),
                uptime=started,
                status=status, status_text=status_text,
                connection_type=typ, encrypted=encrypted, compressed=compressed
            ))

        if len(sessions) == 0 and self.api_version == (14, 7):
            raise NotSupportedError("ejabberd 14.07 always returns an empty list.")

        return sessions

    def stop_user_session(self, username, domain, resource, reason=''):
        self.ctl('kick_session', username, domain, resource, reason)

    def create_user(self, username, domain, password, email=None):
        code, out, err = self.ctl('register', username, domain, password)

        if code == 0:
            try:
                self.set_last_activity(username, domain, status='Registered')
            except BackendError as e:
                log.error('Error setting last activity: %s', e)

            if email is not None:
                self.set_email(username, domain, email)
        elif code == 1:
            raise UserExists()
        else:
            raise BackendError(code)  # TODO: 3 means nodedown.

    def get_last_activity(self, username, domain):
        code, out, err = self.ctl('get_last', username, domain)

        if code != 0:
            raise BackendError(code)

        if six.PY3:
            out = out.decode('utf-8')

        if self.api_version < (17, 4):
            out = out.strip()
            if out == 'Online':
                return datetime.utcnow()
            elif out == 'Never':
                if self.user_exists(username, domain):
                    return None
                raise UserNotFound(username, domain)
            else:
                return datetime.strptime(out[:19], '%Y-%m-%d %H:%M:%S')
        else:
            timestamp, reason = out.strip().split('\t', 1)
            if reason == 'NOT FOUND':
                raise UserNotFound(username, domain)

            if len(timestamp) == 27:
                # NOTE: This format is encountered when the user is not found.
                fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            else:
                fmt = '%Y-%m-%dT%H:%M:%SZ'

            return datetime.strptime(timestamp, fmt)

    def set_last_activity(self, username, domain, status='', timestamp=None):
        timestamp = str(self.datetime_to_timestamp(timestamp))
        code, out, err = self.ctl('set_last', username, domain, timestamp, status)

        if code == 1 and self.api_version >= (16, 1):
            # ejabberd returns status code 1 at least since 16.09
            return
        elif code != 0:
            if code == 1 and self.api_version == (14, 7):
                raise NotSupportedError("ejabberd 14.07 does not support setting last activity.")

            raise BackendError(code)

    def block_user(self, username, domain):
        # 14.07 is really broken here. ban_account fails, and we cannot set a random password
        # either because user_sessions_info doesn't work either and thus we can't stop existing
        # connections. And stopping existing connections doesn't work either.
        code, out, err = self.ctl('ban_account', username, domain, 'Blocked')
        if code != 0:
            if code == 1 and self.api_version == (14, 7):
                raise NotSupportedError("ejabberd 14.07 does not support banning accounts.")

            raise BackendError(code)

    def check_password(self, username, domain, password):
        code, out, err = self.ctl('check_password', username, domain, password)

        if code == 0:
            return True
        elif code == 1:
            return False
        else:
            raise BackendError(code)

    def set_password(self, username, domain, password):
        if self.api_version <= (16, 1, ) and not self.user_exists(username, domain):
            # 16.01 just creates the user upon change_password!
            # NOTE: This may also affect other versions < 16.09.
            raise UserNotFound(username, domain)

        code, out, err = self.ctl('change_password', username, domain, password)
        if six.PY3:
            out = out.decode('utf-8')

        if code == 1 and out == '{not_found,"unknown_user"}\n':
            raise UserNotFound(username, domain)
        elif code != 0:  # 0 is also returned if the user doesn't exist.
            raise BackendError(code)

    def set_unusable_password(self, username, domain):
        code, out, err = self.ctl('ban_account', username, domain, 'by xmpp-account')
        if code != 0:
            raise BackendError(code)

    def message_user(self, username, domain, subject, message):
        """Currently use send_message_chat and discard subject, because headline messages are not stored by
        mod_offline."""
        jid = '%s@%s' % (username, domain)
        if self.api_version <= (14, 7):
            # TODO: it's unclear when send_message was introduced
            command = 'send_message_chat'
            args = domain, '%s@%s' % (username, domain), message
        else:
            command = 'send_message'
            args = 'chat', domain, jid, subject, message

        code, out, err = self.ctl(command, *args)
        if code != 0:
            raise BackendError(code)

    def all_domains(self):
        code, out, err = self.ctl('registered_vhosts')
        if code != 0:
            raise BackendError(code)
        if six.PY3:
            out = out.decode('utf-8')

        return set(out.splitlines())

    def all_users(self, domain):
        code, out, err = self.ctl('registered_users', domain)
        if code != 0:
            raise BackendError(code)

        if six.PY3:
            out = out.decode('utf-8')

        return set(out.splitlines())

    def all_user_sessions(self):
        code, out, err = self.ctl('connected_users_info')
        if code != 0:
            raise BackendError(code)
        out = out.decode('utf-8')  # bytes -> str in py3, str -> unicode in py2
        sessions = set()

        for line in out.splitlines():
            if self.api_version < (18, 6):
                jid, conn, ip, _p, prio, node, uptime = line.split('\t', 6)
                status = ''
                statustext = ''
            else:
                jid, conn, ip, _p, prio, node, uptime, status, resource, statustext = line.split('\t', 9)

            username, domain = jid.split('@', 1)
            domain, resource = domain.split('/', 1)
            if prio == 'nil':
                prio = None
            else:
                prio = int(prio)

            started = pytz.utc.localize(datetime.utcnow() - timedelta(int(uptime)))
            typ, encrypted, compressed = self.parse_connection_string(conn)
            sessions.add(UserSession(
                backend=self,
                username=username,
                domain=domain,
                resource=resource,
                priority=prio,
                ip_address=self.parse_ip_address(ip),
                uptime=started,
                status=status,
                status_text=statustext,
                connection_type=typ, encrypted=encrypted, compressed=compressed
            ))

        return sessions

    def remove_user(self, username, domain):
        code, out, err = self.ctl('unregister', username, domain)
        if code != 0:  # 0 is also returned if the user does not exist
            raise BackendError(code)

    def stats(self, stat, domain=None):
        if stat == 'registered_users':
            stat = 'registeredusers'
        elif stat == 'online_users':
            stat = 'onlineusers'
        else:
            raise ValueError("Unknown stat %s" % stat)

        if domain is None:
            code, out, err = self.ctl('stats', stat)
        else:
            code, out, err = self.ctl('stats_host', stat, domain)

        if code == 0:
            return int(out)
        else:
            raise BackendError(code)
