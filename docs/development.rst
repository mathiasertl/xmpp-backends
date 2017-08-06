###########
Development
###########

**********************************
Using xmpp-backends in development
**********************************

If you use Django, the :py:class:`xmpp_backends.dummy.DummyBackend` uses Djangos caching framework to store
dummy users. In development, simply install **xmpp-backends** and add this to your :file:`settings.py`::

   XMPP_BACKENDS = {
       'default': {
           'BACKEND': 'xmpp_backends.dummy.DummyBackend',
       },
   }

**********************
Write your own backend
**********************

If you want to implement your own backend, all you have to do is implement the
methods from :py:class:`xmpp_backends.base.XmppBackendBase`.

You can test your backend by running ``fab test_backend``::

   fab test_backend:<python-path-to-class>,<domain>[,config_path=/path/to/config.json]

... where ``python-path-to-class`` is the python module path, ``domain`` is the primary domain configured on
that server and ``config_path`` is the path to your config file for the backend. The default ``config_path``
is ``config/<name-of-module>.json``. For example::

   fab test_backend:xmpp_backends.ejabberdctl.EjabberdctlBackend,example.com,config_path=conf/ejabberdctl.json

*******
Testing
*******

There is a small test-suite that can be run with::

   python setup.py test

... but it doesn't assume that you have a running XMPP server. It only has a few basic tests for functions not
related to XMPP and tests if all interfaces actually implement all methods.
