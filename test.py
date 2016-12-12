#!/usr/bin/env python3

import argparse
import importlib
import json
import os
import time

from datetime import datetime

import sleekxmpp


class TestBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.send_presence()
        self.get_roster()


parser = argparse.ArgumentParser('Testscript for testing a backend.')
parser.add_argument('-c', '--config', help='Path to configuration file.')
parser.add_argument('-d', '--domain', default='example.com', help='Test-domain to use.')
parser.add_argument('--host', default='localhost', help='Host for the client to connect to.')
parser.add_argument('-p', '--port', type=int, default=5222,
                    help='Port for the client to connect to.')
parser.add_argument('backend', help='Backend to use.')
args = parser.parse_args()

mod_path, cls_name = args.backend.rsplit('.', 1)
mod = importlib.import_module(mod_path)
cls = getattr(mod, cls_name)

config_path = args.config or os.path.join('config', '%s.json' % mod.__name__.rsplit('.', 1)[-1])
with open(config_path) as stream:
    config = json.load(stream)

backend = cls(**config.get('kwargs', {}))

# no initial users
expected = set(config['expected_users'])
got = backend.all_users(args.domain)
assert got == expected, 'Found initial users: %s vs %s' % (got, expected)

# userdata
username, password, new_password = 'user1', 'password', 'new_password'

# check that the user doesn't exist
assert backend.user_exists(username, args.domain) is False

# Create a user
backend.create_user(username, args.domain, password, 'user@example.net')
got = backend.all_users(args.domain)
expected2 = {'user1', } | expected
assert got == expected2, 'Did not find correct users: %s vs %s' % (got, expected2)
assert backend.check_password(username, args.domain, password)

# set a new password
backend.set_password(username, args.domain, new_password)
assert backend.check_password(username, args.domain, new_password)
assert not backend.check_password(username, args.domain, password)

# set last activity
now = datetime.utcnow().replace(microsecond=0)
backend.set_last_activity(username, args.domain, 'whatever', now)
got = backend.get_last_activity(username, args.domain)
assert got == now, 'Last activity changed: %s -> %s' % (now, got)

# check that the user exists
assert backend.user_exists(username, args.domain) is True

# check that there are no sessions
got = backend.user_sessions(username, args.domain)
assert got == [], got

# check some stats
got = backend.stats('registered_users')
assert got == len(expected2), got
assert backend.stats('registered_users', 'example.com') == len(expected2)
assert backend.stats('online_users') == 0
assert backend.stats('online_users', 'example.com') == 0

jid = '%s@%s' % (username, args.domain)
print('Calling bot...')
bot = TestBot(jid, new_password)
print('Connecting...')
if bot.connect(address=(args.host, args.port, )):
    print('Connected')
    bot.process(block=False)
    print('Processed.')

time.sleep(1)

assert backend.stats('online_users') == 1
assert backend.stats('online_users', 'example.com') == 1

# Remove user, verify that it's gone
backend.remove_user(username, args.domain)
got = backend.all_users(args.domain)
assert got == expected
