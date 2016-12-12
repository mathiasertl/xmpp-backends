# xmpp-backends

**xmpp-backends** provides a set of classes with a common interface to
communicate with admin interfaces of various XMPP servers. This project was
born out of
[django-xmpp-account](https://github.com/mathiasertl/django-xmpp-account/) and
the methods provided are therefor centered around user management. Currently
only ejabberd is supported with communication via the `ejabberdctl` command
line utitlity and via `mod_xmlrpc`.

If you need more functionality and/or other backends please file an issue or
better yet do a pull request.

## Installation

Simply do:

```
pip install xmpp-backends
```

## Supported backends

* `ejabberd_xmlrpc`: Connects to ejabberd via `mod_xmlrpc`. The backend uses
  it's own version of Python's xmlrpc library to correctly encode UTF-8
  characters.
* `ejabberdctl`: Uses the `ejabberdctl` command line utility that obviously
  needs to be available on the local machine.
* `dummy`: Uses Django's chache backend, useful for testing.

## ChangeLog

### 0.3 (to be released)

* Move
  [django-xmpp-backends](https://github.com/mathiasertl/django-xmpp-backends)
  to the `xmpp_backends.django` module.
* Add new commands: `stats`, `get_last_activity`, `user_sessions` and
  `stop_user_session`.
* Implement ``block_user`` for ejabberd backends using the `ban_account`
  command.

### 0.2.1 (2016-09-03)

* ejabberd_xmlrpc backend: Ignore the ``context`` parameter in Python3. The
  parameter is still documented in the official documentation but in fact the
  constructor no longer accepts it.

### 0.2 (2016-04-24)

* Fix import in the dummy backend.
* Release also adds a Python Wheel.

### 0.1 (2015-11-18)

* Initial release.

## License

This project is licensed as GPL v3.0+ except where noted below, see LICENSE
file found in this repository.

* `xmpp_backends/xmlrpclib.py` is a copy of the
  [xmlrpclib](https://docs.python.org/2/library/xmlrpclib.html) module found
  in Python 2.7.10 modified to work to encode UTF-8 characters the way
  ejabberd does. The file is licensed under the same license as the original,
  please see the file itself for details.
