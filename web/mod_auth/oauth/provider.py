"""OAuth 2 Provider Module."""

from web.mod_auth.oauth.storage import get_token_storage
import nova.user
import web.mod_auth.exceptions
import uuid


__provider_storage = None


def get_provider_storage():
    """Get the provider storage instance."""
    global __provider_storage

    if __provider_storage is None:
        __provider_storage = ProviderStorage()

    return __provider_storage


class ProviderStorage(object):
    """
    Provider Storage Container.

    A simple storage for providers. Used to hold multiple providers and return a cached
    provider instance when requested.
    """

    def __init__(self):
        self._providers = {}

    def add(self, provider):
        """Add a new web.mod_auth.oauth.provider.Provider instance."""
        if provider.client_id in self._providers:
            raise web.mod_auth.exceptions.ProviderAlreadyDefinedError('The provider with the client id ' + provider.client_id + ' is already defined.')

        self._providers[provider.client_id] = provider

    def get(self, client_id):
        """Retrieve a stored web,mod_auth.oauth.provider.Provider instance."""
        if client_id not in self._providers:
            raise web.mod_auth.exceptions.ProviderNotDefined('The provider with the client id ' + client_id + ' is not defined.')

        return self._providers[client_id]


class Provider(object):
    """
    OAuth 2 Provider Class.

    Provide an interface to store and retrieve oauth2 tokens and their stored data.

    Positional Arguments
    client_id     -- The id of the client this provider should represent
    client_secret -- The secret to verify this client
    """

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token_storage = get_token_storage().access_tokens
        self.refresh_token_storage = get_token_storage().refresh_tokens

    def authenticate(self, client_secret, grant_type, email=None, password=None, refresh_token=None):
        """
        Authenticate a client/user.

        Based on the grant_type either a client or a user will be authenticated. For client authentication
        only the client_secret and grant_type is required, while for user authentication the client_secret,
        grant_type, email and password are required. This method is also used to refresh expired tokens
        by calling it with the respective grant_type, client_secret and refresh_token.

        Positional Arguments
        client_secret -- The secret to verify the client
        grant_type    -- The grant type to use for authentication

        Keyword Arguments
        email         -- The email of the user to authenticate
        password      -- The password of the user to authenticate
        refresh_token -- A refresh token to request a new access token

        Return
        access_token  -- The access token
        refresh_token -- The refresh token
        """
        if client_secret != self.client_secret:
            raise web.mod_auth.exceptions.WrongClientSecret('The provided client secret is not correct.')

        if grant_type == 'client_credentials':
            access_token = uuid.uuid4().hex
            refresh_token = uuid.uuid4().hex

            data = {}

            self.access_token_storage.add(access_token, data)
            self.refresh_token_storage.add(refresh_token, access_token)
        elif grant_type == 'password':
            user = nova.user.authenticate(email, password)

            if user is None:
                raise web.mod_auth.exceptions.UserCredentialsError('The provided user credentials do not match anything.')

            access_token = uuid.uuid4().hex
            refresh_token = uuid.uuid4().hex

            data = {
                'userid': user['userid'],
                'email': email,
                'role': user['role'],
                'fingerprint': user['fingerprint'],
                'password': user['password']
            }

            self.access_token_storage.add(access_token, data)
            self.refresh_token_storage.add(refresh_token, access_token)
        elif grant_type == 'refresh_token':
            try:
                access_token = self.refresh_token_storage.get(refresh_token)
            except web.mod_auth.exceptions.TokenExpiredError as e:
                access_token = self.refresh_token_storage.get_expired(refresh_token)
                self.refresh_token_storage.delete(refresh_token)
                self.access_token_storage.delete(access_token)

            data = self.access_token_storage.get(access_token)
            self.access_token_storage.delete(access_token)

            access_token = uuid.uuid4().hex
            self.access_token_storage.add(access_token, data)
        else:
            raise web.mod_auth.exceptions.WrongGrantType('The provided grant type is not supported.')

        return access_token, refresh_token

    def is_token_valid(self, token):
        """Return true if the token is valid."""
        try:
            self.access_token_storage.get(token)
        except (web.mod_auth.exceptions.TokenExpiredError, web.mod_auth.exceptions.StorageError) as e:
            return False

        return True

    def is_token_expired(self, token):
        """Return true if the token is expired."""
        try:
            self.access_token_storage.get(token)
        except web.mod_auth.exceptions.TokenExpiredError as e:
            return True

        return False
