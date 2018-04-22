##############
Django support
##############

.. versionadded:: 0.3

   Previously, the module was maintained as a separate project.

The library provides various Django support utilities.

*********************
Backend configuration
*********************

The module ``xmpp_backend.django`` behaves similar to e.g. Djangos cache
configuration. Configure the ``XMPP_BACKENDS`` setting similar to Djangos
default ``CACHES`` setting::

   XMPP_BACKENDS = {
       'default': {
           'BACKEND': 'xmpp_backends.ejabberd_xmlrpc.EjabberdXMLRPCBackend',

           # Any parameters other then "BACKEND" are passed as keyword arguments
           # to the backend constructor:
           'uri': 'https://...',
           'user': 'api-user',
           'server': 'example.com',
           'password': '...',
       },
       'http': {
           'BACKEND': 'xmpp_backends.ejabberd_rest.EjabberdRestBackend',
           'uri': 'https://...',
           'auth': (
               'api-user@example.com',
               '...',
           ),
       },
   }

With that setting, you can access the ``default`` backend like this::

   from xmpp_backends.django import xmpp_backend

... or any of the configured backends::

   from xmpp_backends.django import xmpp_backends
   backend = xmpp_backends['http']

***************
Base user model
***************

.. autoclass:: xmpp_backends.django.models.XmppBackendUser
   :members:


*************************
Authentication middleware
*************************

.. autoclass:: xmpp_backends.django.auth_backends.XmppBackendBackend
   :members:

***********
Development
***********
