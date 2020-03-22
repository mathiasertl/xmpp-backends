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
import subprocess


parser = argparse.ArgumentParser(description="Run the test-suite.")
subparsers = parser.add_subparsers(help='commands', dest='command')
subparsers.add_parser('test', help='Run the test suite.')
subparsers.add_parser('code-quality', help='Test code quality using flake8 and isort.')
args = parser.parse_args()


if args.command == 'code-quality':
    files = ['xmpp_backends', 'setup.py', 'test.py']
    isort = ['isort', '--check-only', '--diff', '-rc'] + files
    print(' '.join(isort))
    subprocess.run(isort, check=True)

    flake8 = ['flake8'] + files
    print(' '.join(flake8))
    subprocess.run(flake8, check=True)
