# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone


class FakeUser(AbstractBaseUser):
    last_activity = models.DateTimeField(default=timezone.now)
