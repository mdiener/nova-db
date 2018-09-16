"""OAuth 2 Storage Module."""

import time
import memcache
import json

from config.web import ACCESS_TOKEN_EXPIRY_TIME, REFRESH_TOKEN_EXPIRY_TIME
from web.mod_auth import exceptions


__storage = None


def get_token_storage():
    """Return the token storage instance."""
    global __storage

    if __storage is None:
        __storage = TokenStorage()

    return __storage


class TokenStorage(object):
    """
    Token Storage Container.

    Access tokens can be accessed through the access_tokens property and refresh tokens
    can be accessed through the refresh_tokens property.
    """

    access_tokens = None
    refresh_tokens = None

    def __init__(self):
        self.access_tokens = Token(ACCESS_TOKEN_EXPIRY_TIME)
        self.refresh_tokens = Token(REFRESH_TOKEN_EXPIRY_TIME)


class Token(object):
    """
    Token Store.

    Simple token store that uses memcache to store the oauth2 tokens.

    Positional Arguments
    expires_in -- Time in seconds when the tokens expire after their creation.
    """

    def __init__(self, expires_in):
        self._expires_in = expires_in
        self._mc = memcache.Client(['127.0.0.1:11211'], debug=0)

    def add(self, token, data):
        """Add data to the token specified by the token."""
        self._mc.set(token, json.dumps({
            'data': data,
            'timestamp': time.time()
        }))

    def get(self, token):
        """Retrieve a token."""
        token_data = self._mc.get(token)

        if token_data is None:
            raise exceptions.StorageError('Could not find the token.')

        if self._expires_in <= 0:
            return json.loads(token_data)

        current_time = time.time()
        if token_data.timestamp + self._expires_in < current_time:
            raise exceptions.TokenExpiredError('The token you tried to retrieve has expired.')

        return json.loads(token_data)

    def get_expired(self, token):
        """Bypass expiration warnings and get token directly."""
        token_data = self._mc.get(token)

        if token_data is None:
            raise exceptions.StorageError('Could not find the token.')

        return json.loads(token_data)

    def delete(self, token):
        """Remove a token."""
        self._mc.delete(token)

    def extend(self, token):
        """Extend a token's lifetime."""
        token_data = self._mc.get(token)
        if token_data is None:
            raise exceptions.StorageError('Could not find the token.')

        token_data = json.loads(token_data)
        token_data['timestamp'] = time.time()

        self._mc.set(token, json.dumps(token_data))
