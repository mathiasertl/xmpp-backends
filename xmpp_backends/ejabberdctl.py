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
from datetime import datetime
from datetime import timedelta
from subprocess import PIPE
from subprocess import Popen

import six

from .base import BackendError
from .base import EjabberdBackendBase
from .base import UserExists
from .base import UserNotFound

log = logging.getLogger(__name__)


class EjabberdctlBackend(EjabberdBackendBase):
    """This backend uses the ejabberdctl command line utility.

    This backend requires ejabberds ``mod_admin_extra`` to be installed.

    .. WARNING::

       This backend is not very secure because ejabberdctl gets any passwords in clear text via the
       commandline. The process list (and thus the passwords) can usually be viewed by anyone that has
       shell-access to your machine!

    :param    path: Optional path to the ``ejabberdctl`` script. The default is ``"/usr/sbin/ejabberdctl"``.
    :param version: A tuple describing the version used, e.g. ``(16, 12,)``. See :ref:`version parameter
        <ejabberd_version>` for a more detailed explanation.
    """

    def __init__(self, path='/usr/sbin/ejabberdctl', version=(17, 7, )):
        self.ejabberdctl = path
        self.version = version

    def get_version(self):
        return self.version

    def ex(self, *cmd):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

    def ctl(self, *cmd):
        return self.ex(self.ejabberdctl, *cmd)

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
        sessions = []

        for line in out.splitlines():
            statustext = ''
            _c, ip, _p, prio, _n, uptime, status, resource = line.split(None, 7)
            if ip.startswith('::FFFF:'):
                ip = ip[7:]
            started = datetime.utcnow() - timedelta(int(uptime))

            if ' ' in resource:
                resource, statustext = resource.split(None, 1)

            sessions.append({
                'ip': ip,
                'priority': int(prio),
                'resource': resource.strip(),
                'started': started,
                'status': status,
                'statustext': statustext,
            })

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
        version = self.get_version()

        if code != 0:
            raise BackendError(code)

        if six.PY3:
            out = out.decode('utf-8')

        if version < (17, 4):
            if out == 'Online':
                return datetime.utcnow()
            elif out == 'Never':
                return None
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
        self.ctl('set_last', username, domain, timestamp, status)

    def block_user(self, username, domain):
        self.ctl('ban_account', username, domain, 'Blocked')

    def check_password(self, username, domain, password):
        code, out, err = self.ctl('check_password', username, domain, password)

        if code == 0:
            return True
        elif code == 1:
            return False
        else:
            raise BackendError(code)

    def set_password(self, username, domain, password):
        code, out, err = self.ctl('change_password', username, domain, password)
        if six.PY3:
            out = out.decode('utf-8')

        if code == 1 and out == '{not_found,"unknown_user"}\n':
            raise UserNotFound(username, domain)
        elif code != 0:  # 0 is also returned if the user doesn't exist.
            raise BackendError(code)

    def set_unusable_password(self, username, domain):
        code, out, err = self.ctl('ban_account', username, domain,
                                  'by django-xmpp-account')
        if code != 0:
            raise BackendError(code)

    def message_user(self, username, domain, subject, message):
        """Currently use send_message_chat and discard subject, because headline messages are not stored by
        mod_offline."""
        self.ctl('send_message_chat', domain, '%s@%s' % (username, domain), message)

    def all_users(self, domain):
        code, out, err = self.ctl('registered_users', domain)
        if code != 0:
            raise BackendError(code)

        if six.PY3:
            out = out.decode('utf-8')

        return set(out.splitlines())

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
