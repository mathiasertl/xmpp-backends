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

.. _ejabberd_version:

The ``version`` parameter
=========================

The ``version`` parameter is common to all `ejabberd <https://www.ejabberd.im/>`_ specific backends
and is used to handle different behaviour among various versions of ejabberd. It is a simple tuple
of integers describing the version, e.g. ``(16, 9, )`` for ejabberd version 16.09.

Currently there are no version specific notes common to all backends, but in the future they will
be listed below. Any version-specific behaviour for a specific backend is noted in the backends own
documentation.

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
