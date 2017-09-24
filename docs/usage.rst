#####
Usage
#####

All interfaces are subclasses of
:py:class:`xmpp_backends.base.XmppBackendBase` and should implement all
methods provided by the baseclass.

Methods concerning a specific user always assume two parameters, the username
and domain of the user. For example::

   >>> user = 'user@example.com'
   >>> username, domain = user.split('@', 1)
   >>> backend.set_password(username, domain, 'random_password')

Backends should shield you from any backend-related exceptions (e.g. exceptions
raised by internal libraries used) and only return one of the exceptions listed
unter :ref:`errors`. This way any code using a backend can cleanly handle any
error conditions. Any method can raise
:py:class:`~xmpp_backends.base.BackendError`, e.g. if the backend is currently
not available. Any method assuming the presence of a user can raise
:py:class:`~xmpp_backends.base.UserNotFound`, any method creating a user can
raise :py:class:`~xmpp_backends.base.UserExists`.

.. autoclass:: xmpp_backends.base.XmppBackendBase
   :members:

.. autoclass:: xmpp_backends.base.UserSession
   :members:

.. _errors:

******
Errors
******

.. autoexception:: xmpp_backends.base.BackendError
   :members:

.. autoexception:: xmpp_backends.base.NotSupportedError
   :members:

.. autoexception:: xmpp_backends.base.InvalidXmppBackendError
   :members:

.. autoexception:: xmpp_backends.base.UserExists
   :members:

.. autoexception:: xmpp_backends.base.UserNotFound
   :members:
