# xmpp-backends

**xmpp-backends** is a Python library and provides a set of classes with a common interface to communicate
with admin interfaces of various XMPP servers. It also includes helper libraries to make it easier to use and
configure with Django.

Detailed documentation is available at http://xmpp-backends.rtfd.org/.

## Installation

Simply do:

```
pip install xmpp-backends
```

## Supported backends

* `ejabberd_rest`: Connects to ejabberd via `mod_http_api`. This is the recommended backend for ejabberd.
* `ejabberd_xmlrpc`: Connects to ejabberd via `mod_xmlrpc`. The backend uses it's own version of Python's
  xmlrpc library to correctly encode UTF-8 characters.
* `ejabberdctl`: Uses the `ejabberdctl` command line utility that obviously needs to be available on the local
  machine.
* `FakeXMPP`: Uses Djangos ORM store data in the database.
* `dummy`: Uses Django's chache backend, useful for testing.

## ChangeLog

### 0.6.0 (TBR)

* Update requirements.
* New ``xmpp_backends.fake_xmpp`` Django app to allow easier development if you're developing a Django app.
* ``ejabberdctl`` backend now also accepts a list of commands to enable running this backend together with an
  ejabberd instance running inside a Docker container.
* Fix autodoc documentation for ``xmpp_backends.django``.
* Test interface based on blacklist of functions, not on whitelist.
* New `fab test_server` command that tests all backends for a specific server.
* `fab test_backend` now starts Docker containers for historic versions of ejabberd.

### 0.5.0 (2017-09-24)

* New methods `all_domains()` and `all_user_sessions()`.
* `user_sessions` now also returns a list of `UserSession` instances, like `all_sessions()`.
* `ipaddress` is now a dependency in Python2.
* Raise `NotImplementedError` if a backend constructor gets an unsupported version.
* `get_last_activity` now raises `UserNotFound` if the user does not exist. In ejabberd < 17.04, this means a
  second API call.
* `set_password` checks if the user exists with ejabberd < 16.01, as ejabberd just creates a user with the
  underlying API call in those versions.
* `block_user()` and `set_last_activity` and `user_sessions()` raise `NotSupportedError` for ejabberd 14.07,
  as the underlying API call is broken in that version.
* Fix `message_user()` to work with all versions.

### 0.4.1 (2017-08-27)

* Raise new `BackendConnectionError` if the backend can't be reached. This case was previously unhandled in 
  the `ejabberd_rest` backend.

### 0.4.0 (2017-08-08)

* Account for API changes in ejabberd 17.04.
* Add a fabfile for common development tasks.
  * Code quality is now checked using [isort](https://github.com/timothycrosley/isort) and
    [flake8](https://gitlab.com/pycqa/flake8) with the `fab check` command.
  * `fab test_backend` now allows you to test a backend. The command is used to assert identical behaviour in
    the various backends.
* Update development requirements.
* Update language quantifiers for setup.py.
* Use [Travis CI](https://travis-ci.org) to run at least some basic in continuous integration.
* Fix `start_user_session` in the dummy backend.
* Fix Python3 support for the `ejabberdctl` backend.
* `set_last_activity` now has an empty default status.
* Various minor fixes in returned values and raised exceptions in all backends.

### 0.3.0 (2016-12-26)

* Move [django-xmpp-backends](https://github.com/mathiasertl/django-xmpp-backends) to the
  `xmpp_backends.django` module.
* New XMPP backend accessing ejabberds REST API interface.
* Add new commands: `stats`, `get_last_activity`, `user_sessions` and `stop_user_session`.
* Implement ``block_user`` for ejabberd backends using the `ban_account` command.
* Add a consistent `version` parameter to handle version-specific behaviour in APIs. 
* The `ejabberdctl` backend now accepts the `path` instead of `EJABBERDCTL_PATH` for consistency with other
  backends.
* Write documentation hosted on
  [http://xmpp-backends.readthedocs.io/](http://xmpp-backends.readthedocs.io/en/latest/index.html).
* Add a test-script that runs the most important commands against a live XMPP server.

### 0.2.1 (2016-09-03)

* ejabberd_xmlrpc backend: Ignore the ``context`` parameter in Python3. The parameter is still documented in
  the official documentation but in fact the constructor no longer accepts it.

### 0.2 (2016-04-24)

* Fix import in the dummy backend.
* Release also adds a Python Wheel.

### 0.1 (2015-11-18)

* Initial release.

## License

This project is licensed as GPL v3.0+ except where noted below, see LICENSE file found in this repository.

* `xmpp_backends/xmlrpclib.py` is a copy of the [xmlrpclib](https://docs.python.org/2/library/xmlrpclib.html)
  module found in Python 2.7.10 modified to work to encode UTF-8 characters the way ejabberd does. The file is
  licensed under the same license as the original, please see the file itself for details.
