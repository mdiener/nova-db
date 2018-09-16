"""
Accessor For Database Operations.

Access the underlying redis database through this module. Permissions and encryption
is handled here, which is why you should be using this class instead of the underlying
connector class.
"""

import json
from config.nova import DATABASE_HOST, DATABASE_PORT, DATABASE
import nova.connector
import nova.pgp
import nova.exceptions

#
# __access_pool = {}
#
#
# def get_accessor(host=DATABASE_HOST, port=DATABASE_PORT, db=DATABASE):
#     """Get an instance of an accessor. If there is no instance for this database, create a new one."""
#     if db not in __access_pool:
#         __access_pool[db] = Accessor(get_connection(host, port, db))
#
#     return __access_pool[db]
#

class Accessor(object):
    """
    Accessor for Database Operations.
    """

    def __init__(self, host=DATABASE_HOST, port=DATABASE_PORT, db=DATABASE):
        """Initialize Accessor."""
        self._db_connection = nova.connector.Connection(host, port, db)

    def exists(self, path, encrypted=False, password=None):
        root = path.split('.')[0]
        path = path[len(root):]

        if encrypted:
            children = path[1:].split('.')

            decrypted_data = self._get_decrypted_data(root, path, password)
            self._exists_in_dict(decrypted_data, children)

        exists = self._db_connection.type(root, path)
        if exists is None:
            return False
        else:
            return True

    def _exists_in_dict(self, data, path):
        if len(path) == 1:
            if path[0] in data:
                return True
            return False
        else:
            return self._exists_in_dict(data[path[0]], path[1:])

    def get(self, path, encrypted=False, userid=None, password=None):
        root = path.split('.')[0]
        path = path[len(root):]

        if not encrypted:
            return self._db_connection.get(root, path)

        if password is None or userid is None:
            raise nova.exceptions.ParameterError('To access an encrypted resource, a userid and corresponding password have to be provided.')

        decrypted_data = self._get_decrypted_data(root, path, userid, password)
        data = self._retrieve_data_from_dict(decrypted_data, path[1:].split('.')[1:])

        return data

    def _load_json(self, data_string):
        try:
            return json.loads(data_string)
        except TypeError as e:
            return None

    def _get_decrypted_data(self, root, path, userid, password):
        children = path[1:].split('.')
        if len(children) < 1:
            raise nova.exceptions.ParameterError('At least two levels for a path have to be provided to access a shared or private resource.')

        encrypted_data = self._db_connection.get(root, children[0])

        try:
            pgp = nova.pgp.OpenPGP
            decrypted_data = pgp.decrypt(encrypted_data, userid, password)
        except nova.exceptions.DecryptionError as e:
            raise nova.exceptions.PermissionError('The provided user does not have access to this resource.')

        return json.loads(decrypted_data)

    def _retrieve_data_from_dict(self, data, path):
        if len(path) == 0:
            return data

        if path[0] not in data:
            raise nova.exceptions.RouteNotDefinedError('Could not find the route to the resource.')

        return self._retrieve_data_from_dict(data[path[0]], path[1:])

    def set(self, path, value, encrypted=False, recipients=[], password=None):
        root = path.split('.')[0]
        path = path[len(root):]

        if encrypted:
            children = path[1:].split('.')

            if not isinstance(recipients, list) and len(recipients) < 1:
                raise nova.exceptions.ParameterError('To save encrypted data you need to provide at least one recipient.')
            if password is None:
                if len(children) > 1:
                    raise nova.exceptions.ParameterError('If you try to set a value inside an encrypted node you have to supply the proper password for decryption.')

                encrypted_data = self._encrypt_data(value, recipients)
            else:
                decrypted_data = self._get_decrypted_data(root, path, password)
                self._set_data_in_dict(value, decrypted_data, children)
                encrypted_data = self._encrypt_data(decrypted_data, recipients)

            self._write_data(root, '.' + children[0], encrypted_data)
        else:
            self._write_data(root, path, value)

    def _set_data_in_dict(self, value, data, path):
        if len(path) == 1:
            data[path[0]] = value
        else:
            self._set_data_in_dict(value, data[path[0]], path[1:])

    def remove(self, path, encrypted=False, password=None, recipients=[]):
        root = path.split('.')[0]
        path = path[len(root):]

        if encrypted:
            children = path[1:].split('.')

            if not isinstance(recipients, list) and len(recipients) < 1:
                raise nova.exceptions.ParameterError('To remove an encrypted key, you need to provide at least one recipient.')

            decrypted_data = self._get_decrypted_data(root, path, password)
            self._remove_key_from_dict(decrypted_data, children)
            encrypted_data = self._encrypt_data(decrypted_data, recipients)

            self._write_data(root, '.' + children[0], encrypted_data)
        else:
            self._db_connection.delete(root, path)

    def _remove_key_from_dict(self, data, path):
        if len(path) == 1:
            del data[path[0]]
        else:
            self._remove_key_from_dict(data[path[0]], path[1:])

    def _encrypt_data(self, value, recipients):
        pgp = nova.pgp.OpenPGP()

        try:
            value = json.dumps(value)
        except ValueError as e:
            raise e

        try:
            return pgp.encrypt(value, recipients)
        except nova.exceptions.EncryptionError as e:
            raise e

    def _write_data(self, root, path, value):
        try:
            self._db_connection.set(root, value, path)
        except (nova.exceptions.ParameterError, nova.exceptions.RedisError) as e:
            raise nova.exceptions.DatabaseWriteError('Could not write to the database. Please try again or contact an administrator if the problem persists.')
