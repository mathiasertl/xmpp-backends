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
from __future__ import print_function
from __future__ import unicode_literals

import importlib
import json
import os
import sys
from datetime import datetime

import pytz
from fabric.api import local
from fabric.api import task
from fabric.colors import green
from fabric.colors import red

from xmpp_backends.base import UserNotFound


def error(msg, status=1):
    print(red(msg))
    sys.exit(status)


def ok(msg='OK.'):
    print(green(msg))


@task
def check():
    """Run code-quality checks."""

    local('isort --check-only --diff -rc xmpp_backends setup.py fabfile.py')
    local('flake8 xmpp_backends/ setup.py fabfile.py')


@task
def test_backend(backend, domain, config_path='', version=''):
    username1 = 'example'
    jid1 = '%s@%s' % (username1, domain)
    password1 = 'foobar'
    password2 = 'barfoo'

    sys.path.insert(0, '.')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
    mod_path, cls_name = backend.rsplit('.', 1)
    importlib.import_module('xmpp_backends')
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)

    config_path = config_path or os.path.join('config', '%s.json' % mod.__name__.rsplit('.', 1)[-1])
    with open(config_path) as stream:
        config = json.load(stream)

    kwargs = config.get('kwargs', {})
    if version:
        kwargs['version'] = tuple(int(t) for t in version.split('.'))

    backend = cls(**config.get('kwargs', {}))
    initial_users = set(config.get('expected_users', set()))

    print('Testing initial state... ', end='')
    users = backend.all_users(domain)
    if users != initial_users:
        error('all_users() did not return expected users: %s' % (users, ))
    if backend.user_exists('example', domain):
        error('User "example" exists.')
    if backend.check_password(username1, domain, password1) is not False:
        error('check_password() did not return False for non-existing user.')
    try:
        ret = backend.get_last_activity(username1, domain)
        error('get_last_activity did not raise UserNotFound: %s' % ret)
    except UserNotFound as e:
        if str(e) != jid1:
            error('UserNotFound from get_last_activity did not match "%s": "%s"' % (jid1, str(e)))
    try:
        backend.set_last_activity(username1, domain)
    except UserNotFound as e:
        # ejabberd api does not indicate any error in this case
        error('set_last_activity raised UserNotFound: %s' % e)

    try:
        backend.set_password(username1, domain, password1)
        error('set_password() did not raise UserNotFound.')
    except UserNotFound as e:
        if str(e) != jid1:
            error('UserNotFound from set_password did not match "%s": "%s"' % (jid1, str(e)))
    all_domains = backend.all_domains()
    if list(sorted(all_domains)) != ['example.com', 'example.net', 'example.org']:
        error('Backend serves wrong domains: %s' % ', '.join(all_domains))
    sessions = backend.all_sessions()
    if sessions != set():
        error('Backend has initial sessions: %s' % sessions)
    ok()

    print('Create and test example user... ', end='')
    if backend.create_user(username1, domain, password1) is not None:
        error('create_user() did not return None.')
    users = backend.all_users(domain)
    if users != {username1, } | initial_users:
        error('Got wrong set of usernames: %s' % (users, ))
    if backend.check_password(username1, domain, password1) is not True:
        error('Could not verify password.')
    if backend.check_password(username1, domain, password2) is not False:
        error('False password is accepted.')
    if backend.set_password(username1, domain, password2) is not None:
        error('set_password() did not return None.')
    if backend.check_password(username1, domain, password2) is not True:
        error('Could not verify password.')
    if backend.check_password(username1, domain, password1) is not False:
        error('False password is accepted.')
    ok()

    print('Test last activity... ', end='')
    backend.get_last_activity(username1, domain)
    now = datetime(2017, 8, 5, 12, 14, 23)
    if backend.set_last_activity(username1, domain, 'foobar', timestamp=now) is not None:
        error('set_last_activity() does not return None.')
    last = backend.get_last_activity(username1, domain)
    if now != last:
        error('Did not get same last activity back: %s vs %s' % (now.isoformat(), last.isoformat()))

    # do same with localized timezone
    tz = pytz.timezone('Europe/Vienna')
    now = tz.localize(now)
    if backend.set_last_activity(username1, domain, 'foobar', timestamp=now) is not None:
        error('set_last_activity() does not return None.')
    last = backend.get_last_activity(username1, domain)
    if now != pytz.utc.localize(last).astimezone(tz):
        error('Did not get same last activity back: %s vs %s' % (now.isoformat(), last.isoformat()))
    ok()

    print('Send user a message... ', end='')
    # message the user - we can not do anything with the message without an XMPP connection, so we just
    # execute it.
    msg = backend.message_user(username1, domain, 'subject', 'message')
    if msg is not None:
        error('message_user() did not return None: %s' % msg)
    ok()

    print('Get (empty) list of user sessions... ', end='')
    sessions = backend.user_sessions(username1, domain)
    if sessions != []:
        error('user_sessions() did not return empty list: %s' % sessions)
    ok()

    # block user
    print('Block user and check previous passwords... ', end='')
    blk = backend.block_user(username1, domain)
    if blk is not None:
        error('block_user() did not return None: %s' % blk)
    if backend.check_password(username1, domain, password1) is not False:
        error('False password is accepted.')
    if backend.check_password(username1, domain, password2) is not False:
        error('False password is accepted.')
    ok()

    # remove user again
    print('Remove user... ', end='')
    if backend.remove_user(username1, domain) is not None:
        error('remove_user() did not return None.')
    if backend.all_users(domain) != initial_users:
        error('all_users() did not return an empty set after removing user.')
    ok()

    print('Test statistics... ', end='')
    stat = backend.stats('registered_users')
    expected_stat = len(initial_users)
    if stat != expected_stat:
        error('registered_users did not return %s: %s' % (expected_stat, stat))
    stat = backend.stats('registered_users', domain)
    if stat != expected_stat:
        error('registered_users for domain did not return %s: %s' % (expected_stat, stat))
    stat = backend.stats('online_users')
    if stat != 0:
        error('online_users did not return 0: %s' % stat)
    stat = backend.stats('online_users', domain)
    if stat != 0:
        error('online_users for domain did not return 0: %s' % stat)
    ok()
