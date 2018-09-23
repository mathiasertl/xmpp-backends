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

"""Common code for XMPP backends."""

from __future__ import unicode_literals

import ipaddress
import logging
import random
import re
import string
import time
from datetime import datetime
from datetime import timedelta
from importlib import import_module

import pytz
import six

from .constants import CONNECTION_HTTP_BINDING
from .constants import CONNECTION_UNKNOWN
from .constants import CONNECTION_XMPP

log = logging.getLogger(__name__)


class BackendError(Exception):
    """All backend exceptions should be a subclass of this exception."""
    pass


class InvalidXmppBackendError(BackendError):
    """Raised when a module cannot be imported."""
    pass


class BackendConnectionError(BackendError):
    """Raised when the backend is unavailable."""
    pass


class NotSupportedError(BackendError):
    """Raised when a backend does not support a specific function.

    This error may be thrown only with specific versions, e.g. if it requires minimum version.
    """
    pass


class UserExists(BackendError):
    """Raised when a user already exists."""
    pass


class UserNotFound(BackendError):
    """Raised when a user is not found."""

    def __init__(self, node, domain, resource=None):
        self.node = node
        self.domain = domain
        self.resource = resource

    def __str__(self):
        s = '%s@%s' % (self.node, self.domain)
        if self.resource is not None:
            s += '/%s' % self.resource
        return s


@six.python_2_unicode_compatible
class UserSession(object):
    """An object describing a user session.

    :param         backend: The XMPP backend used for retrieving this session.
    :param        username: The username of the user.
    :type         username: str
    :param          domain: The domain of the user.
    :type           domain: str
    :param        resource: The resource of the user.
    :param        priority: The priority of this connection.
    :param      ip_address: The IP address of this connection.
    :param          uptime: A timestamp of when this connection came online.
    :param          status: The status message for this connection (e.g. "I am available.").
    :param connection_type: The type of connection.
    :param       encrypted: If this connection is encrypted. This may be ``None`` if the backend is not able
        decide if the connection is encrypted (e.g. if it is a HTTP bind connection).
    :param      compressed: If this connection uses XMPP stream compression. This is always ``None`` for
        connections where this is not applicable, e.g. Websocket connections.
    """
    def __init__(self, backend, username, domain, resource, priority, ip_address, uptime, status, status_text,
                 connection_type, encrypted, compressed):
        # make sure that data is in unicode
        if six.PY2 is True:
            if isinstance(username, six.binary_type):
                username = username.decode('utf-8')
            if isinstance(domain, six.binary_type):
                domain = domain.decode('utf-8')
            if isinstance(resource, six.binary_type):
                resource = resource.decode('utf-8')
            if isinstance(status_text, six.binary_type):
                status_text = status_text.decode('utf-8')

        self._backend = backend
        self.username = username
        self.domain = domain
        self.jid = '%s@%s' % (username, domain)
        self.resource = resource
        self.priority = priority
        self.ip_address = ip_address
        self.uptime = uptime
        self.status = status
        self.status_text = status_text
        self.connection_type = connection_type
        self.encrypted = encrypted
        self.compressed = compressed

    def __eq__(self, other):
        return isinstance(other, UserSession) and self.jid == other.jid and self.resource == other.resource

    def __hash__(self):
        return hash((self.jid, self.resource))

    def __str__(self):
        return '%s@%s/%s' % (self.username, self.domain, self.resource)

    def __repr__(self):
        val = '<UserSession: %s@%s/%s>' % (self.username, self.domain, self.resource)
        if six.PY2 is True:
            return val.encode('utf-8')
        return val


class XmppBackendBase(object):
    """Base class for all XMPP backends."""

    library = None
    """Import-party of any third-party library you need.

    Set this attribute to an import path and you will be able to access the module as ``self.module``. This
    way you don't have to do a module-level import, which would mean that everyone has to have that library
    installed, even if they're not using your backend.

    :param version_cache_timeout: How long the API version for this backend will be cached.
    :type  version_cache_timeout: int or timedelta

    """
    _module = None

    minimum_version = None
    version_cache_timeout = None
    version_cache_timestamp = None
    version_cache_value = None

    def __init__(self, version_cache_timeout=3600):
        if isinstance(version_cache_timeout, int):
            version_cache_timeout = timedelta(seconds=version_cache_timeout)
        self.version_cache_timeout = version_cache_timeout
        super(XmppBackendBase, self).__init__()

    @property
    def module(self):
        """The module specified by the ``library`` attribute."""

        if self._module is None:
            if self.library is None:
                raise ValueError(
                    "Backend '%s' doesn't specify a library attribute" % self.__class__)

            try:
                if '.' in self.library:
                    mod_path, cls_name = self.library.rsplit('.', 1)
                    mod = import_module(mod_path)
                    self._module = getattr(mod, cls_name)
                else:
                    self._module = import_module(self.library)
            except (AttributeError, ImportError):
                raise ValueError("Couldn't load %s backend library" % cls_name)

        return self._module

    def datetime_to_timestamp(self, dt):
        """Helper function to convert a datetime object to a timestamp.

        If datetime instance ``dt`` is naive, it is assumed that it is in UTC.

        In Python 3, this just calls ``datetime.timestamp()``, in Python 2, it substracts any timezone offset
        and returns the difference since 1970-01-01 00:00:00.

        Note that the function always returns an int, even in Python 3.

        >>> XmppBackendBase().datetime_to_timestamp(datetime(2017, 9, 17, 19, 59))
        1505678340
        >>> XmppBackendBase().datetime_to_timestamp(datetime(1984, 11, 6, 13, 21))
        468595260

        :param dt: The datetime object to convert. If ``None``, returns the current time.
        :type  dt: datetime
        :return: The seconds in UTC.
        :rtype: int
        """
        if dt is None:
            return int(time.time())

        if six.PY3:
            if not dt.tzinfo:
                dt = pytz.utc.localize(dt)
            return int(dt.timestamp())
        else:
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None) - dt.utcoffset()
            return int((dt - datetime(1970, 1, 1)).total_seconds())

    def get_random_password(self, length=32, chars=None):
        """Helper function that gets a random password.

        :param length: The length of the random password.
        :type  length: int
        :param  chars: A string with characters to choose from. Defaults to all ASCII letters and digits.
        :type   chars: str
        """
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for x in range(length))

    @property
    def api_version(self):
        """Cached version of :py:func:`~xmpp_backends.base.XmppBackendBase.get_api_version`."""

        now = datetime.utcnow()

        if self.version_cache_timestamp and self.version_cache_timestamp + self.version_cache_timeout > now:
            return self.version_cache_value  # we have a cached value

        self.version_cache_value = self.get_api_version()

        if self.minimum_version and self.version_cache_value < self.minimum_version:
            raise NotSupportedError('%s requires ejabberd >= %s' % (self.__class__.__name__,
                                                                    self.minimum_version))

        self.version_cache_timestamp = now
        return self.version_cache_value

    def get_api_version(self):
        """Get the API version used by this backend.

        Note that this function is usually not invoked directly but through
        :py:attr:`~xmpp_backends.base.XmppBackendBase.api_version`.

        The value returned by this function is used by various backends to determine how to call various API
        backends and/or how to parse th data returned by them. Backends generally assume that this function is
        always working and return the correct value.

        If your backend implementation cannot get this value, it should be passed via the constructor and
        statically returned for the livetime of the instance.
        """

        raise NotImplementedError

    def user_exists(self, username, domain):
        """Verify that the given user exists.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :return: ``True`` if the user exists, ``False`` if not.
        :rtype: bool
        """

        raise NotImplementedError

    def user_sessions(self, username, domain):
        """Get a list of all current sessions for the given user.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :return: A list :py:class:`~xmpp_backends.base.UserSession` describing the user sessions.
        :rtype: list of :py:class:`~xmpp_backends.base.UserSession`
        """

        raise NotImplementedError

    def stop_user_session(self, username, domain, resource, reason=''):
        """Stop a specific user session, identified by its resource.

        A resource uniquely identifies a connection by a specific client.

        :param   username: The username of the user.
        :type    username: str
        :param     domain: The domain of the user.
        :type      domain: str
        :param   resource: The resource of the connection
        :type    resource: str
        """

        raise NotImplementedError

    def create_user(self, username, domain, password, email=None):
        """Create a new user.

        :param username: The username of the new user.
        :type  username: str
        :param   domain: The domain of the new user.
        :type    domain: str
        :param password: The password of the new user.
        :param    email: The email address provided by the user.
        """
        raise NotImplementedError

    def create_reservation(self, username, domain, email=None):
        """Reserve a new account.

        This method is called when a user account should be reserved, meaning that the account can no longer
        be registered by anybody else but the user cannot yet log in either. This is useful if e.g. an email
        confirmation is still pending.

        The default implementation calls :py:func:`~xmpp_backends.base.XmppBackendBase.create_user` with a
        random password.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :param    email: The email address provided by the user. Note that at this point it is not confirmed.
            You are free to ignore this parameter.
        """
        password = self.get_random_password()
        self.create(username=username, domain=domain, password=password, email=email)

    def confirm_reservation(self, username, domain, password, email=None):
        """Confirm a reservation for a username.

        The default implementation just calls :py:func:`~xmpp_backends.base.XmppBackendBase.set_password` and
        optionally :py:func:`~xmpp_backends.base.XmppBackendBase.set_email`.
        """
        self.set_password(username=username, domain=domain, password=password)
        if email is not None:
            self.set_email(username=username, domain=domain, email=email)

    def check_password(self, username, domain, password):
        """Check the password of a user.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :param password: The password to check.
        :type  password: str
        :return: ``True`` if the password is correct, ``False`` if not.
        :rtype: bool
        """
        raise NotImplementedError

    def set_password(self, username, domain, password):
        """Set the password of a user.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :param password: The password to set.
        :type  password: str
        """
        raise NotImplementedError

    def get_last_activity(self, username, domain):
        """Get the last activity of the user.

        The datetime object returned should be a naive datetime object representing the time in UTC.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :return: A naive datetime object in UTC representing the last activity.
        :rtype: datetime
        """
        raise NotImplementedError

    def set_last_activity(self, username, domain, status='', timestamp=None):
        """Set the last activity of the user.

        .. NOTE::

           If your backend requires a Unix timestamp (seconds since 1970-01-01), you can use the
           :py:func:`~xmpp_backends.base.XmppBackendBase.datetime_to_timestamp` convenience function to
           convert it to an integer.

        :param  username: The username of the user.
        :type   username: str
        :param    domain: The domain of the user.
        :type     domain: str
        :param    status: The status text.
        :type     status: str
        :param timestamp: A datetime object representing the last activity. If the object is not
            timezone-aware, assume UTC. If ``timestamp`` is ``None``, assume the current date and time.
        :type  timestamp: datetime
        """
        raise NotImplementedError

    def block_user(self, username, domain):
        """Block the specified user.

        The default implementation calls :py:func:`~xmpp_backends.base.XmppBackendBase.set_password` with a
        random password.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        """
        self.set_password(username, domain, self.get_random_password())

    def set_email(self, username, domain, email):
        """Set the email address of a user."""
        raise NotImplementedError

    def check_email(self, username, domain, email):
        """Check the email address of a user.

        **Note:** Most backends don't implement this feature.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        """
        raise NotImplementedError

    def expire_reservation(self, username, domain):
        """Expire a username reservation.

        This method is called when a reservation expires. The default implementation just calls
        :py:func:`~xmpp_backends.base.XmppBackendBase.remove_user`. This is fine if you do not override
        :py:func:`~xmpp_backends.base.XmppBackendBase.create_reservation`.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        """
        self.remove_user(username, domain)

    def message_user(self, username, domain, subject, message):
        """Send a message to the given user.

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :param  subject: The subject of the message.
        :param  message: The content of the message.
        """
        pass

    def all_users(self, domain):
        """Get all users for a given domain.

        :param   domain: The domain of interest.
        :type    domain: str
        :return: A set of all users. The usernames do not include the domain, so ``user@example.com`` will
            just be ``"user"``.
        :rtype: set of str
        """
        raise NotImplementedError

    def all_domains(self):
        """List of all domains used by this backend.

        :return: List of all domains served by this backend.
        :rtype: list of str
        """
        raise NotImplementedError

    def all_user_sessions(self):
        """List all current user sessions.

        :param domain: Optionally only return sessions for the given domain.
        :return: A list :py:class:`~xmpp_backends.base.UserSession` for all sessions.
        :rtype: list of :py:class:`~xmpp_backends.base.UserSession`
        """

        raise NotImplementedError

    def remove_user(self, username, domain):
        """Remove a user.

        This method is called when the user explicitly wants to remove her/his account.

        :param username: The username of the new user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        """
        raise NotImplementedError

    def stats(self, stat, domain=None):
        """Get statistical value about the XMPP server.

        Minimal statistics that should be supported is ``"registered_users"`` and ``"online_users"``. The
        specific backend might support additional stats.

        :param stat: The value of the statistic.
        :type  stat: str
        :param domain: Limit statistic to the given domain. If not listed, give statistics
                       about all users.
        :type  domain: str
        :return: The current value of the requested statistic.
        :rtype: int
        """
        raise NotImplementedError


class EjabberdBackendBase(XmppBackendBase):
    """Base class for ejabberd related backends.

    This class overwrites a few methods common to all ejabberd backends.
    """

    minimum_version = (14, 7)

    def parse_version_string(self, version):
        return tuple(int(t) for t in version.split('.'))

    def parse_status_string(self, data):
        match = re.search(r'([^ ]*) is running in that node', data)
        if not match:
            raise BackendError('Could not determine API version.')

        return self.parse_version_string(match.groups()[0].split('-', 1)[0])

    def has_usable_password(self, username, domain):
        """Always return ``True``.

        In ejabberd there is no such thing as a "banned" account or an unusable password. Even ejabberd's
        ``ban_account`` command only sets a random password that the user could theoretically guess.
        """

        return True

    def set_email(self, username, domain, email):
        """Not yet implemented."""
        pass

    def check_email(self, username, domain, email):
        """Not yet implemented."""
        pass

    def parse_connection_string(self, connection):
        """Parse string as returned by the ``connected_users_info`` or ``user_sessions_info`` API calls.

        >>> EjabberdBackendBase().parse_connection_string('c2s_tls')
        (0, True, False)
        >>> EjabberdBackendBase().parse_connection_string('c2s_compressed_tls')
        (0, True, True)
        >>> EjabberdBackendBase().parse_connection_string('http_bind')
        (2, None, None)

        :param connection: The connection string as returned by the ejabberd APIs.
        :type  connection: str
        :return: A tuple representing the conntion type, if it is encrypted and if it uses XMPP stream
            compression.
        :rtype: tuple
        """
        # TODO: Websockets, HTTP Polling
        if connection == 'c2s_tls':
            return CONNECTION_XMPP, True, False
        elif connection == 'c2s_compressed_tls':
            return CONNECTION_XMPP, True, True
        elif connection == 'http_bind':
            return CONNECTION_HTTP_BINDING, None, None
        elif connection == 'c2s':
            return CONNECTION_XMPP, False, False
        log.warn('Could not parse connection string "%s"', connection)
        return CONNECTION_UNKNOWN, True, True

    def parse_ip_address(self, ip_address):
        """Parse an address as returned by the ``connected_users_info`` or ``user_sessions_info`` API calls.

        Example::

            >>> EjabberdBackendBase().parse_ip_address('192.168.0.1')  # doctest: +FORCE_TEXT
            IPv4Address('192.168.0.1')
            >>> EjabberdBackendBase().parse_ip_address('::FFFF:192.168.0.1')  # doctest: +FORCE_TEXT
            IPv4Address('192.168.0.1')
            >>> EjabberdBackendBase().parse_ip_address('::1')  # doctest: +FORCE_TEXT
            IPv6Address('::1')

        :param ip_address: An IP address.
        :type  ip_address: str
        :return: The parsed IP address.
        :rtype: `ipaddress.IPv6Address` or `ipaddress.IPv4Address`.
        """
        if ip_address.startswith('::FFFF:'):
            ip_address = ip_address[7:]
        if six.PY2 and isinstance(ip_address, str):
            # ipaddress constructor does not eat str in py2 :-/
            ip_address = ip_address.decode('utf-8')

        return ipaddress.ip_address(ip_address)
