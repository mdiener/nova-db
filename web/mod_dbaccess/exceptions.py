from web.exceptions import WebError


class UserAccessError(WebError):
    pass


class NotAUUIDError(WebError):
    pass
