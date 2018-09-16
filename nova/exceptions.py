class NovaError(Exception):
    def __init__(self, message):
        self.message = message


class CMDLineError(NovaError):
    pass


class ConnectorError(NovaError):
    pass


class ParameterError(ConnectorError):
    pass


class RedisError(ConnectorError):
    pass


class ValueError(NovaError):
    pass


class EmailConnectionFailed(NovaError):
    pass


class KeyError(NovaError):
    pass


class EncryptionError(KeyError):
    pass


class DecryptionError(KeyError):
    pass


class KeyUnlockError(KeyError):
    pass


class UserError(NovaError):
    pass


class EditUserError(UserError):
    pass


class UserExistsError(UserError):
    pass


class UserNotFoundError(UserError):
    pass


class AlreadyVerifiedError(UserError):
    pass


class PermissionError(UserError):
    pass


class DBAccessError(NovaError):
    pass


class RootNodeNotDefinedError(DBAccessError):
    pass


class RouteNotDefinedError(DBAccessError):
    pass


class DatabaseWriteError(DBAccessError):
    pass


class ManagerError(NovaError):
    pass


class RootAlreadyExistsError(ManagerError):
    pass
