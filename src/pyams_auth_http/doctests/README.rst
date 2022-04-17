=================================
PyAMS HTTP authentication package
=================================


Introduction
------------

This package is composed of a set of utility functions, usable into any Pyramid application.
It's an extension to PyAMS_security, which allows extraction of user's credentials from HTTP
"Authorization" headers:

    >>> import pprint

    >>> from pyramid.testing import tearDown, DummyRequest
    >>> from pyams_security.tests import setup_tests_registry, new_test_request
    >>> config = setup_tests_registry()
    >>> config.registry.settings['zodbconn.uri'] = 'memory://'

    >>> from pyramid_zodbconn import includeme as include_zodbconn
    >>> include_zodbconn(config)
    >>> from cornice import includeme as include_cornice
    >>> include_cornice(config)
    >>> from pyams_utils import includeme as include_utils
    >>> include_utils(config)
    >>> from pyams_mail import includeme as include_mail
    >>> include_mail(config)
    >>> from pyams_site import includeme as include_site
    >>> include_site(config)
    >>> from pyams_security import includeme as include_security
    >>> include_security(config)
    >>> from pyams_auth_http import includeme as include_auth_http
    >>> include_auth_http(config)

    >>> from pyams_utils.registry import get_utility, set_local_registry
    >>> registry = config.registry
    >>> set_local_registry(registry)

    >>> from pyams_site.generations import upgrade_site
    >>> request = DummyRequest()
    >>> app = upgrade_site(request)
    Upgrading PyAMS timezone to generation 1...
    Upgrading PyAMS security to generation 2...

    >>> from zope.traversing.interfaces import BeforeTraverseEvent
    >>> from pyams_utils.registry import handle_site_before_traverse
    >>> handle_site_before_traverse(BeforeTraverseEvent(app, request))

    >>> from pyams_security.interfaces import ISecurityManager
    >>> sm = get_utility(ISecurityManager)

    >>> from pyams_security.interfaces.plugin import ICredentialsPlugin
    >>> plugin = get_utility(ICredentialsPlugin, name='http-basic')


Using PyAMS security policy
---------------------------

The plugin should be included correctly into PyAMS security policy:

    >>> from pyramid.authorization import ACLAuthorizationPolicy
    >>> config.set_authorization_policy(ACLAuthorizationPolicy())

    >>> from pyams_security.policy import PyAMSAuthenticationPolicy
    >>> policy = PyAMSAuthenticationPolicy(secret='my secret',
    ...                                    http_only=True,
    ...                                    secure=False)
    >>> config.set_authentication_policy(policy)

Getting effective principals via security policy require a Beaker cache:

    >>> from beaker.cache import CacheManager, cache_regions
    >>> cache = CacheManager(**{'cache.type': 'memory'})
    >>> cache_regions.update({'short': {'type': 'memory', 'expire': 0}})
    >>> cache_regions.update({'long': {'type': 'memory', 'expire': 0}})

    >>> plugin in sm.credentials_plugins
    True
    >>> plugin in sm.authentication_plugins
    False
    >>> plugin in sm.directory_plugins
    False

    >>> request = new_test_request('{system}.admin', 'admin', registry=config.registry)
    >>> policy.unauthenticated_userid(request)
    'system:admin'
    >>> policy.authenticated_userid(request)
    'system:admin'


Extracting credentials from request
-----------------------------------

The main feature of this plugin is to extract credentials from HTTP Authorization header:

    >>> import base64
    >>> encoded = base64.encodebytes(b'john:doe').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> request.headers.get('Authorization')
    'Basic am9objpkb2U=\n'

    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True

Credentials are set to None because the given credentials can't be authenticated!
We can extract credentials without authenticating them:

    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request, authenticate=False)
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
    >>> creds = plugin.extract_credentials(request, authenticate=False)
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
    >>> creds = plugin.extract_credentials(request, authenticate=False)
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

    >>> encoded = base64.encodebytes(b'{system}.admin:admin').decode()
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
    'admin'

This should not work with bad credentials:

    >>> encoded = base64.encodebytes(b'{system}.admin:john').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Basic {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True

Authentication methods other than "Basic" are not actually supported:

    >>> encoded = base64.encodebytes(b'john:doe').decode()
    >>> request = DummyRequest(headers={'Authorization': 'Digest {}'.format(encoded)})
    >>> creds = plugin.extract_credentials(request)
    >>> creds is None
    True

    >>> sorted(policy.effective_principals(request))
    ['system.Everyone']

    >>> request = new_test_request('{system}.admin', 'admin', registry=config.registry)
    >>> sorted(policy.effective_principals(request))
    ['system.Authenticated', 'system.Everyone', 'system:admin']


Tests cleanup:

    >>> tearDown()
