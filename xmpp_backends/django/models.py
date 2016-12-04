# -*- coding: utf-8 -*-
#
# This file is part of django-xmpp-register (https://account.jabber.at/doc).
#
# django-xmpp-register is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# django-xmpp-register is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# django-xmpp-register.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from . import backend
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _



class XmppBackendUser(AbstractBaseUser):
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def exists(self):
        return backend.user_exists(self.node, self.domain)

    def set_password(self, raw_password):
        if raw_password is None:
            self.set_unusable_password()
        else:
            backend.set_password(self.node, self.domain, raw_password)

    def check_password(self, raw_password):
        return backend.check_password(self.node, self.domain, raw_password)

    def set_unusable_password(self):
        backend.block_user(self.node, self.domain)

    def get_short_name(self):
        return self.node

    @property
    def node(self):
        return self.get_username().split('@', 1)[0]

    @property
    def domain(self):
        return self.get_username().split('@', 1)[1]

