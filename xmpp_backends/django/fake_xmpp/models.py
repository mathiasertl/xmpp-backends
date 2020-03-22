# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends. If not, see
# <http://www.gnu.org/licenses/>.

from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from ...constants import CONNECTION_HTTP_BINDING
from ...constants import CONNECTION_HTTP_POLLING
from ...constants import CONNECTION_UNKNOWN
from ...constants import CONNECTION_WEBSOCKETS
from ...constants import CONNECTION_XMPP


class FakeUser(AbstractBaseUser):
    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    last_status = models.CharField(max_length=255, blank=True, null=True)
    is_blocked = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = _('Fake XMPP User')
        verbose_name_plural = _('Fake XMPP Users')

    @property
    def node(self):
        return self.username.split('@', 1)[0]

    @property
    def domain(self):
        return self.username.split('@', 1)[1]

    def message(self, subject, message, sender):
        self.messages.create(subject=subject, message=message, sender=sender)


class FakeUserSession(models.Model):
    user = models.ForeignKey(FakeUser, models.CASCADE, related_name='sessions')
    resource = models.CharField(max_length=255, default=get_random_string)
    priority = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')
    uptime = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255)
    status_text = models.CharField(max_length=255)
    connection_type = models.SmallIntegerField(choices=(
        (CONNECTION_XMPP, _('XMPP')),
        (CONNECTION_HTTP_POLLING, _('HTTP Polling')),
        (CONNECTION_HTTP_BINDING, _('HTTP Binding')),
        (CONNECTION_WEBSOCKETS, _('Websockets')),
        (CONNECTION_UNKNOWN, _('Unkown')),
    ))
    encrypted = models.NullBooleanField()
    compressed = models.NullBooleanField()

    class Meta:
        verbose_name = _('Fake XMPP Session')
        verbose_name_plural = _('Fake XMPP Sessions')


class FakeUserMessage(models.Model):
    user = models.ForeignKey(FakeUser, models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=64)
    date = models.DateTimeField(default=timezone.now)
    subject = models.CharField(max_length=12)
    message = models.CharField(max_length=128)
