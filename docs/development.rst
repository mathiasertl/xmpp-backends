###########
Development
###########

**********************************
Using xmpp-backends in development
**********************************

The :py:class:`xmpp_backends.dummy.DummyBackend` uses Djangos caching framework
to store dummy users. In development, simply install **xmpp-backends** and add
this to your :file:`settings.py`::

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

*******
Testing
*******

There is a small test-suite that can be run with::

   python -m unittest discover

... but it doesn't assume that you have a running XMPP server. It only tests
wether all interfaces actually implement all methods.

Test script
===========

To actually test a backend, there is a script called ``test.py`` in the root
directory. It's a simple script that creates a backend instance and calls the
most important functions and checks their return values.

To run the script, you need `SleekXMPP <https://github.com/fritzy/SleekXMPP>`_
(``pip install sleekxmpp``) installed.

The script assumes that the XMPP server used by the backend is running on
localhost, servers the domain ``example.com`` and, if there is authentication
required, a user named ``api@example.com`` with the password ``example`` has
access to everything.

The only required argument is the full python path to the backend class::

   python test.py xmpp_backends.ejabberdctl.EjabberdctlBackend
   python test.py xmpp_backends.ejabberd_xmlrpc.EjabberdXMLRPCBackend
   python test.py xmpp_backends.ejabberd_rest.EjabberdRestBackend

The arguments the backend is instantiated with are in the ``config`` directory,
you can override the file with the ``--config`` option. If your XMPP server is
not running on localhost, use ``--host`` and ``--port``  as parameters.

Start ejabberd for test script
==============================

There is a working ejabberd config in ``config/ejabberd.yml``. To get a running
instance, simply do::

   apt-get install -y ejabberd
   cp config/ejabberd.yml /etc/ejabberd/
   /etc/init.d/ejabberd start
   ejabberdctl register api example.com example
