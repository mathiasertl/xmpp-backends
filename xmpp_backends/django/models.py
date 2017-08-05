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

from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _

from . import xmpp_backend


class XmppBackendUser(AbstractBaseUser):
    """An abstract base model using xmpp as backend for various functions.

    The model assumes that the username as returned by :py:func:`get_username` is the full JID of the user.
    """

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def exists(self):
        return xmpp_backend.user_exists(self.node, self.domain)

    def set_password(self, raw_password):
        """Calls :py:func:`~xmpp_backends.base.XmppBackendBase.set_password` for the user.

        If password is ``None``, calls :py:func:`~xmpp_backends.base.XmppBackendBase.set_unusable_password`.
        """
        if raw_password is None:
            self.set_unusable_password()
        else:
            xmpp_backend.set_password(self.node, self.domain, raw_password)

    def check_password(self, raw_password):
        """Calls :py:func:`~xmpp_backends.base.XmppBackendBase.check_password` for the user."""
        return xmpp_backend.check_password(self.node, self.domain, raw_password)

    def set_unusable_password(self):
        """Calls :py:func:`~xmpp_backends.base.XmppBackendBase.ban_account` for the user."""

        xmpp_backend.block_user(self.node, self.domain)

    def get_short_name(self):
        """An alias for ``node``."""

        return self.node

    @property
    def node(self):
        """The node-part of the username.

        Example::

            >>> u = XmppBackendUser(username='user@example.com')
            >>> u.node
            'user'
        """
        return self.get_username().split('@', 1)[0]

    @property
    def domain(self):
        """The domain-part of the username.

        Example::

            >>> u = XmppBackendUser(username='user@example.com')
            >>> u.domain
            'example.com'
        """
        return self.get_username().split('@', 1)[1]
