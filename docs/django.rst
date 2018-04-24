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

Fake XMPP server
================

If you want to develop a Django project and don't want to run a real XMPP server
on your development server, you can use the ``fake_xmpp`` app. Simply enable it
in ``INSTALLED_APPS`` and configure a your ``XMPP_BACKENDS``::

   INSTALLED_APPS = [
       #...
       'xmpp_backends.django.fake_xmpp',
   ]

   XMPP_BACKENDS = {
    'default': {
        'BACKEND': 'xmpp_backends.django.fake_xmpp.backend.FakeXMPPBackend',
        'domains': ['example.com', 'example.net', 'example.org'],
        'version': (1, 0),  # doesn't do anything, reserved for future use.
    },

The app also adds all models to the admin interface, so you can add users etc. there.

.. autoclass:: xmpp_backends.django.fake_xmpp.backend.FakeXMPPBackend

Dummy backend
=============

.. autoclass:: xmpp_backends.dummy.DummyBackend
