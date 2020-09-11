=================================
PyAMS HTTP authentication package
=================================

Introduction
------------

This package is composed of a set of utility functions, usable into any Pyramid application.

    >>> from pyramid.testing import setUp, tearDown, DummyRequest
    >>> config = setUp()

    >>> from pyams_auth_http import includeme as include_auth_http
    >>> include_auth_http(config)

    >>> from pyams_security.interfaces import ICredentialsPlugin
    >>> plugin = config.registry.getUtility(ICredentialsPlugin, name='http-basic')

    >>> import base64
    >>> encoded = base64.encodebytes(b'john:doe').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> request.headers.get('Authorization')
    'Basic am9objpkb2U=\n'

    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'http'
    >>> creds.id
    'john'
    >>> creds.attributes.get('login')
    'john'
    >>> creds.attributes.get('password')
    'doe'

We can also handle passwords containing a semicolon:

    >>> encoded = base64.encodebytes(b'john:doe:pwd').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'http'
    >>> creds.id
    'john'
    >>> creds.attributes.get('login')
    'john'
    >>> creds.attributes.get('password')
    'doe:pwd'


Passwords with encoded characters should be also accepted:

    >>> encoded = base64.encodebytes('john:pass@àé'.encode('latin1')).decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'http'
    >>> creds.id
    'john'
    >>> creds.attributes.get('login')
    'john'
    >>> creds.attributes.get('password')
    'pass@àé'


Providing a request without authorization, or a bad encoded authorization header, should return
None:

    >>> request = DummyRequest()
    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True

    >>> request = DummyRequest(headers={'Authorization': 'Basic not encoded'})
    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True


This plugin also provides a custom login management feature, which allows to give a prefix to
a login, using braces followed by a dot:

    >>> encoded = base64.encodebytes(b'{system}.admin:john').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds
    <pyams_security.credential.Credentials object at 0x...>
    >>> creds.prefix
    'http'
    >>> creds.id
    'system:admin'
    >>> creds.attributes.get('login')
    'admin'
    >>> creds.attributes.get('password')
    'john'


Authentication methods other than "Basic" are not actually supported:

    >>> encoded = base64.encodebytes(b'john:doe').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Digest {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True


Tests cleanup:

    >>> tearDown()
