# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends. If
# not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin

from .models import FakeUser
from .models import FakeUserMessage
from .models import FakeUserSession


class SessionInline(admin.TabularInline):
    model = FakeUserSession


class MessageInline(admin.TabularInline):
    model = FakeUserMessage


@admin.register(FakeUser)
class FakeUserAdmin(admin.ModelAdmin):
    inlines = [MessageInline, SessionInline, ]
    fields = ['username', 'email', 'password', ('last_login', 'last_activity'), 'last_status', 'is_blocked']
