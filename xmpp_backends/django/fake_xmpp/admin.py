# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import FakeUser
from .models import FakeUserSession


class SessionInline(admin.TabularInline):
    model = FakeUserSession


@admin.register(FakeUser)
class FakeUserAdmin(admin.ModelAdmin):
    inlines = [SessionInline, ]
    fields = ['username', 'email', 'password', ('last_login', 'last_activity'), 'last_status', 'is_blocked']
