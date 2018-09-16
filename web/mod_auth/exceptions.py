from web.exceptions import WebError


class AuthError(WebError):
    pass


class StorageError(AuthError):
    pass


class ProviderError(AuthError):
    pass


class ProviderAlreadyDefinedError(ProviderError):
    pass


class ProviderNotDefined(ProviderError):
    pass


class WrongClientSecret(ProviderError):
    pass


class RefreshTokenInvalid(StorageError):
    pass


class TokenExpiredError(StorageError):
    pass


class WrongGrantType(ProviderError):
    pass


class UserCredentialsError(ProviderError):
    pass
