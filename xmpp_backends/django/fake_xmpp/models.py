# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class FakeUser(AbstractBaseUser):
    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    last_status = models.CharField(max_length=255, blank=True, null=True)
    is_blocked = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'

    @property
    def node(self):
        return self.username.split('@', 1)[0]

    @property
    def domain(self):
        return self.username.split('@', 1)[1]


class FakeUserSession(models.Model):
    user = models.ForeignKey(FakeUser, models.CASCADE, related_name='sessions')
    resource = models.CharField(max_length=255, default=get_random_string)
    priority = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')
    uptime = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255)
    status_text = models.CharField(max_length=255)
    connection_type = models.SmallIntegerField()
    encrypted = models.NullBooleanField()
    compressed = models.NullBooleanField()
