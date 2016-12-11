#!/usr/bin/env python3

import argparse
import importlib
import json
import os

from datetime import datetime

parser = argparse.ArgumentParser('Testscript for testing a backend.')
parser.add_argument('-c', '--config', help='Path to configuration file.')
parser.add_argument('-d', '--domain', default='example.com', help='Test-domain to use.')
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

# Create a user
username, password, new_password = 'user1', 'password', 'new_password'
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

# Remove user, verify that it's gone
backend.remove_user(username, args.domain)
got = backend.all_users(args.domain)
assert got == expected
