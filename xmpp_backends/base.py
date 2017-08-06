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

import random
import string
import time
from datetime import datetime
from importlib import import_module

import pytz
import six


class BackendError(Exception):
    """All backend exceptions should be a subclass of this exception."""
    pass


class InvalidXmppBackendError(BackendError):
    """Raised when a module cannot be imported."""
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


class XmppBackendBase(object):
    """Base class for all XMPP backends."""

    library = None
    """Import-party of any third-party library you need.

    Set this attribute to an import path and you will be able to access the module as ``self.module``. This
    way you don't have to do a module-level import, which would mean that everyone has to have that library
    installed, even if they're not using your backend.
    """
    _module = None

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

        In Python 3, this just calls ``datetime.timestamp()`, in Python 2, it substracts any timezone offset
        and returns the difference since 1970-01-01 00:00:00.

        Note that the function always returns an int, even in Python 3.

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
        """Get a list of user sessions.

        The function returns a list of dictionaries each describing a presence connection.

        ========== ===============================================================================
        key        Description
        ========== ===============================================================================
        ip         The IP the user is connected with, as a ``str``.
        priority   The users priority, an ``int``.
        started    When the session was started, a ``datetime`` in the UTC timezone.
        status     The current status, e.g. ``"available"``.
        resource   The resource used in the connection.
        statustext The status text, if any. If the user does not have a presence text, the value
                   is an empty string.
        ========== ===============================================================================

        :param username: The username of the user.
        :type  username: str
        :param   domain: The domain of the user.
        :type    domain: str
        :return: A list of connections, each list element is a dictionary with the keys ``"ip"``,
            ``"priority"``, ``"uptime"``, ``"status"``, ``"resource"`` and ``"statustext"``.  See above for
            more information.
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
