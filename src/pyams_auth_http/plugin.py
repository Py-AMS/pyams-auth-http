#
# Copyright (c) 2008-2015 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_auth_http.plugin module

This module defines an HTTP authentication module.
"""

import base64
import re

from pyams_security.credential import Credentials
from pyams_security.interfaces import ISecurityManager
from pyams_security.interfaces.plugin import ICredentialsPlugin
from pyams_utils.registry import query_utility, utility_config
from pyams_utils.wsgi import wsgi_environ_cache


__docformat__ = 'restructuredtext'

from pyams_auth_http import _  # pylint: disable=ungrouped-imports


PARSED_CREDENTIALS_ENVKEY = "pyams_auth_http.credentials.basic"

CUSTOM_LOGIN = re.compile(r'^{(.*)}\.?(.*)')


@utility_config(name='http-basic', provides=ICredentialsPlugin)
class HttpBasicCredentialsPlugin:
    """HTTP basic credentials plug-in

    This credential plug-in is mainly used by automation processes using
    XML-RPC or JSON-RPC requests launched from batch scripts.

    Copied from pyramid_httpauth package.
    """

    prefix = 'http'
    title = _("HTTP basic authentication")
    enabled = True

    @wsgi_environ_cache(PARSED_CREDENTIALS_ENVKEY, store_none=False)
    def extract_credentials(self, request, **kwargs):  # pylint: disable=unused-argument
        """Extract login/password credentials from given request"""
        auth = request.headers.get('Authorization')
        if not auth:
            return None
        try:
            scheme, params = auth.split(' ', 1)
            if scheme.lower() != 'basic':
                return None
            token_bytes = base64.b64decode(params.strip())
            try:
                token = token_bytes.decode('utf-8')
            except UnicodeDecodeError:
                token = token_bytes.decode('latin-1')
            login, password = token.split(':', 1)
            if login.startswith('{'):
                principal_id = CUSTOM_LOGIN.sub(r'\1:\2', login)
                prefix, login = principal_id.split(':')  # pylint: disable=unused-variable
            else:
                principal_id = login
            # validate credentials
            credentials = Credentials(self.prefix, principal_id,
                                      login=login, password=password)
            if not kwargs.get('authenticate', True):
                return credentials
            sm = query_utility(ISecurityManager)  # pylint: disable=invalid-name
            if sm is not None:
                principal_id = sm.authenticate(credentials, request)
                if principal_id is not None:
                    credentials.id = principal_id
                    return credentials
            return None
        except (ValueError, TypeError):
            return None
