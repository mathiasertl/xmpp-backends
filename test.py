#!/usr/bin/env python3

import argparse
import datetime
import importlib
import json
import os

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

backend = cls(**config)

# no initial users
assert backend.all_users(args.domain) == [], 'Found initial users.'

# Create a user
username, password, new_password = 'user1', 'password', 'new_password'
backend.create_user(username, args.domain, password, 'user@example.net')
assert backend.all_users(args.domain) == ['user1'], 'Did not find correct users.'
assert backend.check_password(username, args.domain, password)

# set a new password
backend.set_password(username, args.domain, new_password)
assert backend.check_password(username, args.domain, new_password)
assert not backend.check_password(username, args.domain, password)

# set last activity
now = datetime.utcnow()
backend.set_last_activity(username, args.domain, 'whatever', now)
assert backend.get_last_activity(username, args.domain, now) == now

# Remove user, verify that it's gone
backend.remove_user(args.username, args.domain)
assert backend.all_users(args.domain) == []
