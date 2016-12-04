# -*- coding: utf-8 -*-
#
# This file is part of django-xmpp-backends (https://github.com/mathiasertl/django-xmpp-backends).
#
# django-xmpp-backends s free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# django-xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# django-xmpp-backends.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from . import backend

User = get_user_model()


class XmppBackendBackend(object):
    def authenticate(self, username, password):
        try:
            user = User.objects.get(**{User.USERNAME_FIELD: username, })

            node, domain = username.split('@', 1)
            if backend.check_password(node, domain, password):
                return user
        except User.DoesNotExist:
            pass

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
