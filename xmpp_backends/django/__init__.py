# -*- coding: utf-8 -*-
#
# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends.  If
# not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, absolute_import

from importlib import import_module
from threading import local

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_BACKEND_ALIAS = 'default'
__all__ = [
    'backend', 'DEFAULT_BACKEND_ALIAS', 'InvalidXmppBackendError',
]


class InvalidXmppBackendError(ImproperlyConfigured):
    pass


def _get_backend(backend, **kwargs):
    try:
        conf = settings.XMPP_BACKENDS[backend]
        params = conf.copy()
        params.update(kwargs)
        backend = params.pop('BACKEND')

        mod_path, cls_name = backend.rsplit('.', 1)
        mod = import_module(mod_path)
        backend_cls = getattr(mod, cls_name)
    except (KeyError, AttributeError, ImportError) as e:
        raise InvalidXmppBackendError(
            "Could not find backend '%s': %s" % (backend, e))
    backend = backend_cls(**params)
    return backend


class BackendHandler(object):
    """A Cache Handler to manage access to Cache instances.

    Ensures only one instance of each alias exists per thread.

    This implementation is an adaption of django.core.cache.BackendHandler.
    """
    def __init__(self):
        self._backends = local()

    def __getitem__(self, alias):
        try:
            return self._backends.backends[alias]
        except AttributeError:
            self._backends.backends = {}
        except KeyError:
            pass

        if alias not in settings.XMPP_BACKENDS:
            raise InvalidXmppBackendError(
                "Could not find config for '%s' in settings.XMPP_BACKENDS" % alias
            )

        backend = _get_backend(alias)
        self._backends.backends[alias] = backend
        return backend

    def all(self):
        return getattr(self._backends, 'backends', {}).values()


xmpp_backends = BackendHandler()


class DefaultBackendProxy(object):
    """Proxy access to the default backend object's attributes.

    This allows the `backend` object to be thread-safe using the `backends` API.

    This implementation is an adaption of django.core.cache.DefaultCacheProxy.
    """
    def __getattr__(self, name):
        return getattr(xmpp_backends[DEFAULT_BACKEND_ALIAS], name)

    def __setattr__(self, name, value):
        return setattr(xmpp_backends[DEFAULT_BACKEND_ALIAS], name, value)

    def __delattr__(self, name):
        return delattr(xmpp_backends[DEFAULT_BACKEND_ALIAS], name)

    def __contains__(self, key):
        return key in xmpp_backends[DEFAULT_BACKEND_ALIAS]

    def __eq__(self, other):
        return xmpp_backends[DEFAULT_BACKEND_ALIAS] == other

    def __ne__(self, other):
        return xmpp_backends[DEFAULT_BACKEND_ALIAS] != other


xmpp_backend = DefaultBackendProxy()
