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

"""Common code for XMPP backends."""

from __future__ import unicode_literals

import string
import random

from importlib import import_module


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
    pass


class XmppBackendBase(object):
    """Base class for all XMPP backends."""

    library = None
    """Import-party of any third-party library you need.

    Set this attribute to an import path and you will be able to access the module as
    ``self.module``. This way you don't have to do a module-level import, which would mean that
    everyone has to have that library installed, even if they're not using your backend.
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

    def get_random_password(self, length=32, chars=None):
        """Helper function that gets a random password.

        :param length: The length of the random password.
        :param  chars: A string with characters to choose from. Defaults to all
            ASCII letters and digits.
        """
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for x in range(length))

    def user_exists(self, username, domain):
        """Return `True` if the user exists, `False` otherwise."""

        raise NotImplementedError

    def create_user(self, username, domain, password, email=None):
        """Create a new user.

        :param    username: The username of the new user.
        :param      domain: The selected domain, may be any domain provided
                            in :ref:`settings-XMPP_HOSTS`.
        :param    password: The password of the new user.
        :param       email: The email address provided by the user.
        """
        raise NotImplementedError

    def create_reservation(self, username, domain, email=None):
        """Reserve a new account.

        This method is called when a user account should be reserved, meaning that the account can
        no longer be registered by anybody else but the user cannot yet log in either. This is
        useful if e.g. an email confirmation is still pending.

        The default implementation calls :py:func:`~xmpp_backends.base.XmppBackendBase.create` with
        a random password.

        :param username: The username of the new user.
        :param   domain: The selected domain, may be any domain provided
                         in :ref:`settings-XMPP_HOSTS`.
        :param    email: The email address provided by the user. Note that at this point it is not
                         confirmed. You are free to ignore this parameter.
        """
        password = self.get_random_password()
        self.create(username=username, domain=domain, password=password, email=email)

    def confirm_reservation(self, username, domain, password, email=None):
        """Confirm a reservation for a username.

        The default implementation just calls `set_password()` and optionally `set_email()`.
        """
        self.set_password(username=username, domain=domain, password=password)
        if email is not None:
            self.set_email(username=username, domain=domain, email=email)

    def check_password(self, username, domain, password):
        """Check the password of a user.

        :param username: The username of the new user.
        :param   domain: The selected domain, may be any domain provided
                         in :ref:`settings-XMPP_HOSTS`.
        :param password: The password to check.
        :return: ``True`` if the password is correct, ``False`` otherwise.
        """
        raise NotImplementedError

    def set_password(self, username, domain, password):
        """Set the password of a user.

        :param username: The username of the new user.
        :param   domain: The selected domain, may be any domain provided
                         in :ref:`settings-XMPP_HOSTS`.
        :param password: The password to set.
        """
        raise NotImplementedError

    def set_last_activity(self, username, domain, status, timestamp=None):
        """Set the last activity of the user.

        :param  username: The username of the new user.
        :param    domain: The selected domain, may be any domain provided
                         in :ref:`settings-XMPP_HOSTS`.
        :param    status: The status text.
        :param timestamp: The timestamp as returned by `time.time()`. If omitted, the current time
            is used.
        """
        raise NotImplementedError

    def block_user(self, username, domain):
        """Called when a user is blocked.

        The default implementation calls :py:func:`set_password` with a random password.
        """
        self.set_password(username, domain, self.get_random_password())

    def set_email(self, username, domain, email):
        """Set the email address of a user."""
        raise NotImplementedError

    def check_email(self, username, domain, email):
        """Check the email address of a user."""
        raise NotImplementedError

    def expire_reservation(self, username, domain):
        """Expire a username reservation.

        This method is called when a reservation expires. The default implementation just calls
        :py:func:`~backends.base.XmppBackendBase.remove`. This is fine if you do not override
        :py:func:`~backends.base.XmppBackendBase.reserve`.
        """
        self.remove(username, domain)

    def message_user(self, username, domain, subject, message):
        """Send a message to the given user."""
        pass

    def all_users(self, domain):
        """Get all users for a given domain.

        :param   domain: The domain of interest.
        :returns: A set of all users. The usernames do not include the domain, so
            `user@example.com` will just be `user`.
        """
        raise NotImplementedError

    def remove_user(self, username, domain):
        """Remove a user.

        This method is called when the user explicitly wants to remove her/his account.

        :param username: The username of the new user.
        :param   domain: The domainname selected, may be any domainname
                         provided in :ref:`settings-XMPP_HOSTS`.
        """
        raise NotImplementedError
