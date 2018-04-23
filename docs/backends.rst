##################
Supported backends
##################

Currently all backends are designed to work with various ejabberd APIs. If you want to support a
different XMPP server, please don't hesitate to `file an issue
<https://github.com/mathiasertl/xmpp-backends/issues>`_.

*****************
ejabberd REST API
*****************

.. autoclass:: xmpp_backends.ejabberd_rest.EjabberdRestBackend
   :members:

*******************
ejabberd XMLRPC API
*******************

.. autoclass:: xmpp_backends.ejabberd_xmlrpc.EjabberdXMLRPCBackend
   :members:

Version-specific notes
======================

* **ejabberd <= 17.03**: The ``get_last`` API call did not indicate if the user existed or not.
  :py:class:`~xmpp_backends.base.get_last_activity` will return ``None`` if the user does not exist.
  
  .. seealso:: `GitHub issue <https://github.com/processone/ejabberd/issues/1565>`_

* **ejabberd <= 14.07**: Encoding of UTF-8 characters in ejabberd <= 14.07 is handled in the same
  way as the standard PHP XMLRPC library does. **xmpp-backends** includes a hacked version of
  ``xmlrpclib`` to handle the behaviour, but the hack is not enabled for Python 3.

***********
ejabberdctl
***********

.. autoclass:: xmpp_backends.ejabberdctl.EjabberdctlBackend
   :members:

***********************
ejabberd specific notes
***********************

.. _ejabberd-required-commands:

Required commands
=================

ejabberd allows you to restrict the commands usable at a specific endpoint.  **xmpp-backends**
currently uses these commands:

* change_password
* check_account
* check_password
* connected_users_info
* get_last
* kick_session
* register
* registered_users
* registered_vhosts
* send_message/send_message_chat
* set_last
* stats
* stats_host
* status
* unregister
* user_sessions_info

.. _ejabberd_version:

The ``version`` parameter
=========================

The ``version`` parameter is common to all `ejabberd <https://www.ejabberd.im/>`_ specific backends
and is used to handle different behaviour among various versions of ejabberd. It is a simple tuple
of integers describing the version, e.g. ``(16, 9, )`` for ejabberd version 16.09.

Version-specific notes
======================

* **ejabberd <= 17.03:** Ejabberd 17.03 and earlier return the timestamp for
  ``get_last_activity`` in the system timezone, not UTC. See `this github issue
  <https://github.com/processone/ejabberd/issues/1565>`_.
* **ejabberd <= 16.01:** :py:func:`~xmpp_backends.base.XmppBackendBase.set_password`
  does a second API call verifying that the user exists, as the underlying API
  call (``change_password``) creates the user if it doesn't exist.
* **ejabberd <= 14.07:** :py:func:`~xmpp_backends.base.XmppBackendBase.block_user` and
  :py:func:`~xmpp_backends.base.XmppBackendBase.all_user_sessions` will raise
  :py:class:`~xmpp_backends.base.NotSupportedError`, as the underlying API call is known to be broken.
  


``EjabberdBackendBase``
=======================

The :py:class:`~xmpp_backends.base.EjabberdBackendBase` class is the base class for all `ejabberd
<https://www.ejabberd.im/>`_ specific backends. It implements some common methods:

.. autoclass:: xmpp_backends.base.EjabberdBackendBase
   :show-inheritance:
   :members:

.. _ejabberd_tls:

ejabberd TLS setup
==================

**xmpp-backends** is written for https://jabber.at, which prides itself in a good TLS setup. Our
full configuration is available `on github <https://github.com/jabber-at/config>`_.

At present, we essentially do what is listed in the example below, but please also check our github
config for the most recent version::

   define_macro:
     # check most recent version from github:
     #    https://github.com/jabber-at/config/blob/master/ejabberd.yml
     'TLS_OPTIONS':
       - "no_sslv2"
       - "no_sslv3"
     'TLS_CIPHERS': "ECDH:DH:!CAMELLIA128:!3DES:!MD5:!RC4:!aNULL:!NULL:!EXPORT:!LOW:!MEDIUM"

   s2s_access: authenticated
   s2s_certfile: "/etc/..."
   s2s_use_starttls: required
   s2s_protocol_options: 'TLS_OPTIONS'
   s2s_ciphers: 'TLS_CIPHERS'

   # create dhfile with (takes a LONG time!):
   #     openssl dhparam -out ... 4096
   s2s_dhfile: "/etc/ejabberd/dhparams"

   listen:
     - ip: ...
       # XMPP c2s connections:
       #starttls_required: true
       # Any HTTPS connections:
       #tls: true
       protocol_options: 'TLS_OPTIONS'
       ciphers: 'TLS_CIPHERS'
       dhfile: "/etc/ejabberd/dhparams"
