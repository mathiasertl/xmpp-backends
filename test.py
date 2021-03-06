#!/usr/bin/env python3
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

import argparse
import importlib
import ipaddress
import os
import shlex
import subprocess
import sys
import threading
import time
import warnings
from datetime import datetime

import coverage
import django
import pytz
import yaml
from django.core.management import call_command
from sleekxmpp import ClientXMPP

parser = argparse.ArgumentParser(description="Run the test-suite.")
subparsers = parser.add_subparsers(help='commands', dest='command')
subparsers.add_parser('test', help='Run the test suite.')
server_parser = subparsers.add_parser('test-server', help='Run the test suite.')
server_parser.add_argument('server', help="The server to test.")
server_parser.add_argument('version', help="The server version to test.")
subparsers.add_parser('code-quality', help='Test code quality using flake8 and isort.')
args = parser.parse_args()


def error(msg, status=1):
    print(msg)
    sys.exit(status)


def ok(msg='OK.'):
    print(msg)


def start_bot(jid, password, host, port):
    #import logging
    #logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

    class EchoBot(ClientXMPP):
        def __init__(self, jid, password, *args, **kwargs):
            ClientXMPP.__init__(self, jid=jid, password=password, *args, **kwargs)

            self.add_event_handler("session_start", self.start)
            self.add_event_handler("message", self.message)
            self.auto_reconnect = False  # to make sure that a killed session does not reconnect

        def start(self, event):
            self.send_presence()
            self.get_roster()

        def message(self, msg):
            if msg['type'] in ('chat', 'normal'):
                msg.reply("Thanks for sending\n%(body)s" % msg).send()

    xmpp = EchoBot(jid, password)

    def process():
        xmpp.process(block=True)

    xmpp.connect((host, port), use_tls=False)
    thread = threading.Thread(target=xmpp.process, kwargs={'block': True})
    thread.start()
    return xmpp, thread


def test_session(backend, version, session, username, domain, status='available', status_text=''):
    assert session.username == username, 'Username: "%s" vs "%s"' % (session.username, username)
    assert session.domain == domain, 'Domain does not match'
    if version >= (18, 6):
        assert session.status == status, 'Status does not match: "%s" vs "%s"' % (session.status, status)
        assert session.status_text == status_text, 'Status Text does not match: "%s" vs "%s"' % (
            session.status_text, status_text)
    assert isinstance(session.ip_address, (ipaddress.IPv4Address, ipaddress.IPv6Address))
    assert isinstance(session.uptime, datetime)
    assert isinstance(session.priority, int)
    assert session.priority >= 0


def test_user_sessions(backend, version, username, domain, resource, password):
    from xmpp_backends.base import NotSupportedError

    print('Start tests requiring a running session... ', end='')
    xmpp = None
    if hasattr(backend, 'start_user_session'):
        # Some backends (like the dummy backend) expose a method to start a "session".
        backend.start_user_session(username, domain, resource, ip_address='127.0.0.1')
    else:
        jid = '%s@%s/%s' % (username, domain, resource)
        xmpp, thread = start_bot(jid, password, host='localhost', port='5222')
        time.sleep(1)  # wait for connection to establish

    try:
        user_sessions = backend.user_sessions(username, domain)
    except NotSupportedError:
        pass  # we already notified about this earlier.
    else:
        if len(user_sessions) != 1:
            error('Found wrong number of user sessions (1): %s' % user_sessions)
        session = list(user_sessions)[0]
        test_session(backend, version, session, username, domain)

    try:
        sessions = backend.all_user_sessions()
    except NotSupportedError:
        pass  # we already notified about this earlier.
    else:
        if len(sessions) != 1:
            error('Found wrong number of user sessions (2): %s' % sessions)
        session = list(sessions)[0]
        test_session(backend, version, session, username, domain)

    # Stop session again and see that it's gone
    backend.stop_user_session(username, domain, resource)

    if xmpp is not None:
        xmpp.disconnect()

    try:
        sessions = backend.all_user_sessions()
    except NotSupportedError:
        pass  # we already notified about this earlier.
    else:
        if sessions != set():
            error('Session not correctly stopped: %s' % sessions)

    try:
        user_sessions = backend.user_sessions(username, domain)
    except NotSupportedError:
        pass  # we already notified about this earlier.
    else:
        if user_sessions != set():
            error('Found wrong number of user sessions (3): %s' % user_sessions)
    ok()


def _test_backend(cls, config, version):
    from xmpp_backends.base import NotSupportedError
    from xmpp_backends.base import UserNotFound

    username1 = 'example'
    resource1 = 'resource1'
    domain = 'example.com'
    jid1 = '%s@%s' % (username1, domain)
    password1 = 'foobar'
    password2 = 'barfoo'

    kwargs = config.get('KWARGS', {})

    try:
        backend = cls(**kwargs)
    except NotImplementedError as e:
        print(e)
        return

    initial_users = set(config.get('EXPECTED_USERS', set()))

    print('Testing API version... ', end='')
    if version != backend.api_version:
        error('API version returned %s, but should have returned %s.' % (version, backend.api_version))
    ok()

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
    except NotSupportedError:
        pass  # We have a separate line for that later
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
    try:
        sessions = backend.all_user_sessions()
    except NotSupportedError:  # 15.07 is broken
        pass  # We have a separate line for that later
    else:
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

    try:
        print('Test last activity... ', end='')
        last = backend.get_last_activity(username1, domain)
        if last is not None and not isinstance(last, datetime):
            error('Last of new user is not None: %s' % last)

        now = datetime(2017, 8, 5, 12, 14, 23)
        if backend.set_last_activity(username1, domain, 'foobar', timestamp=now) is not None:
            error('set_last_activity() does not return None.')
        last = backend.get_last_activity(username1, domain)
        if now != last:
            error('Did not get same last activity back: %s vs %s' % (now, last))

        # do same with localized timezone
        tz = pytz.timezone('Europe/Vienna')
        now = tz.localize(now)
        if backend.set_last_activity(username1, domain, 'foobar', timestamp=now) is not None:
            error('set_last_activity() does not return None.')
        last = backend.get_last_activity(username1, domain)
        if now != pytz.utc.localize(last).astimezone(tz):
            error('Did not get same last activity back: %s vs %s' % (now.isoformat(), last.isoformat()))
        ok()
    except NotSupportedError as e:
        print(e)

    print('Send user a message... ', end='')
    # message the user - we can not do anything with the message without an XMPP connection, so we just
    # execute it.
    msg = backend.message_user(username1, domain, 'subject', 'message')
    if msg is not None:
        error('message_user() did not return None: %s' % msg)
    ok()

    print('Send message to non-existing user...', end='')
    try:
        msg = backend.message_user('wrong-username', domain, 'subject', 'message')
        ok()
    except UserNotFound as e:
        # ejabberd api does not indicate any error in this case
        error('set_last_activity raised UserNotFound: %s' % e)

    try:
        print('Get (empty) list of user sessions... ', end='')
        sessions = backend.user_sessions(username1, domain)
    except NotSupportedError as e:
        print(e)
    else:
        if sessions != set():
            error('user_sessions() did not return empty set: %s' % sessions)
        ok()

    try:
        test_user_sessions(backend, version, username1, domain, resource1, password2)
    finally:
        backend.stop_user_session(username1, domain, resource1)

    # block user
    try:
        print('Block user and check previous passwords... ', end='')
        blk = backend.block_user(username1, domain)
    except NotSupportedError as e:
        print(e)
    else:
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


def test_backend(backend, domain, config_path='', version=''):
    docker_name = 'xmpp-backends-docker'

    sys.path.insert(0, '.')

    with open(os.path.join('config', 'backends.yaml')) as stream:
        config = yaml.load(stream.read(), Loader=yaml.SafeLoader)
    config = config.get(backend, {})

    # Add any version-specific config overrides
    overrides = config.get('VERSION_OVERRIDES', {})
    if version in overrides:
        config.update(overrides[version])

    for key, value in config.get('ENVIRONMENT', {}).items():
        os.environ.setdefault(key, value)

    # unsure if we need this
    if config.get('PYTHONPATH'):
        sys.path.insert(0, config['PYTHONPATH'])

    # Setup Django (Before import of class, otherwise import might fail)
    if config.get('DJANGO_SETUP', False):
        import django
        django.setup()

        if config.get('DJANGO_MIGRATE', False):
            call_command('migrate')

    # import the class
    mod_path, cls_name = backend.rsplit('.', 1)
    importlib.import_module('xmpp_backends')
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)

    # test any minimum version requirements
    parsed_version = tuple(int(t) for t in version.split('.'))
    if cls.minimum_version and parsed_version < cls.minimum_version:
        print('Backend does not support version %s of XMPP server.' % version)
        return

    # Start docker container if requested
    docker = config.get('DOCKER', False)
    if docker:
        path = os.path.join(os.getcwd(), 'config', '%s-%s' % (config['SERVER'], version))
        container = '%s:%s' % (docker['container'], version)
        cmd = ['docker', 'pull', container]
        print('+ %s' % ' '.join(cmd))
        subprocess.run(cmd, check=True)

        cmd = ['docker', 'run', '--rm', '-d', '--name=%s' % docker_name, '--mount',
               'type=bind,source=%s,target=/etc/ejabberd' % path]
        for port in docker.get("ports", [5222, 5223, 5269, ]):
            cmd += ['-p', '%s:%s/tcp' % (port, port)]
        cmd.append(container)
        print('+ %s' % ' '.join(cmd))
        subprocess.run(cmd, check=True)

    for cmd in config.get('BEFORE_TEST', []):
        context = {}
        if docker:
            context["DOCKER_CONTAINER"] = docker_name
        cmd = shlex.split(cmd % context)
        print('+ %s' % ' '.join(cmd))
        subprocess.run(cmd, check=True)

    try:
        _test_backend(cls, config, parsed_version)
    finally:
        if docker:
            subprocess.run(['docker', 'kill', docker_name])


if args.command == 'code-quality':
    files = ['xmpp_backends', 'setup.py', 'test.py', 'tests']
    isort = ['isort', '--check-only', '--diff', '-rc'] + files
    print(' '.join(isort))
    subprocess.run(isort, check=True)

    flake8 = ['flake8'] + files
    print(' '.join(flake8))
    subprocess.run(flake8, check=True)

    warnings.simplefilter("error")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
    django.setup()
    call_command('check')
elif args.command == 'test-server':
    with open(os.path.join('config', 'backends.yaml')) as stream:
        config = yaml.load(stream.read(), Loader=yaml.SafeLoader)

    backends = {k: v for k, v in config.items() if v.get('SERVER') == args.server}

    for backend in backends:
        print('Test %s' % backend)
        test_backend(backend, 'example.com', version=args.version)
elif args.command == 'test':
    rootdir = os.path.dirname(os.path.realpath(__file__))
    report_dir = os.path.join(rootdir, 'docs', '_build', 'coverage')
    cov = coverage.Coverage(
        cover_pylib=False, branch=True, source=['xmpp_backends'],
        omit=['*migrations/*',
              'xmpp_backends/ejabberdctl.py',
              'xmpp_backends/ejabberd_xmlrpc.py',
              'xmpp_backends/ejabberd_rest.py']
    )
    cov.start()

    warnings.simplefilter("error")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
    django.setup()
    call_command('test', 'tests')

    cov.stop()
    cov.save()
    total_coverage = cov.html_report(directory=report_dir)
    print('Test coverage: %.2f%%' % total_coverage)
else:
    parser.print_usage()
