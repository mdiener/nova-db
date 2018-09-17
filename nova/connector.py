"""Low Level Connector Interface."""

from numbers import Number

import json
import redis

import nova.exceptions
from config.nova import DATABASE_HOST, DATABASE_PORT, DATABASE

#
# __connection_pool = {}
#
#
# def get_connection(host=DATABASE_HOST, port=DATABASE_PORT, db=DATABASE):
#     """Retrieve underlying connection pool to Redis Database."""
#     if db not in __connection_pool:
#         __connection_pool[db] = Connection(host, port, db)
#
#     return __connection_pool[db]
#

class Connection(object):
    """
    Lower Level Connection Class.

    Please don't use this directly, but rather use the provided nova.accessor.Accessor class.

    To write and read values to the redis database, you can specify a key and provide data. Since
    we assume we're using redis as a json store (with the reJSON extension) you can also specify
    a path to access. For example given the following structure:
    key: foo
    value: {
        'myobj': {
            'mysubkey': 'A test.'
        }
    }
    You can access mysubkey with the following call: Connection.get('foo', '.myobj.mysubkey')
    """

    def __init__(self, host=DATABASE_HOST, port=DATABASE_PORT, db=DATABASE):
        """
        Low level connection class.

        Keyword Arguments
        host -- The host of the redis database
        port -- The port of the redis database
        db   -- The redis database number
        """
        self._client = redis.StrictRedis(host=host, port=port, db=db)

    def set(self, key, value, path='.'):
        """
        Set the value specified by key and path.

        Positional Arguments
        key   -- The top level key to set
        value -- The value to write

        Keyword Arguments
        path -- The path to write to after the key
        """
        if not isinstance(key, str):
            raise nova.exceptions.ParameterError('The provided key is not a string.')

        if not isinstance(path, str):
            raise nova.exceptions.ParameterError('The provided path is not a string.')

        if path == '':
            path = '.'

        value = json.dumps(value)

        try:
            self._client.execute_command('JSON.SET', key, path, value)
        except redis.exceptions.RedisError as e:
            raise nova.exceptions.RedisError('Something went wrong with the redis connection.')

    def get(self, key, path='.'):
        """
        Retrieve the value specified by key and path.

        Positional Arguments
        key -- The key to access

        Keyword Arguments
        path -- The path to retrieve the value from.
        """
        if not isinstance(key, str):
            raise nova.exceptions.ParameterError('The provided key is not a string.')

        if not isinstance(path, str):
            raise nova.exceptions.ParameterError('The provided path is not a string.')

        if path == '':
            path = '.'

        if self.type(key, path) is None:
            return None

        try:
            byteval = self._client.execute_command('JSON.GET', key, path)
        except redis.exceptions.RedisError as e:
            raise nova.exceptions.RedisError('Something went wrong with the redis connection.')

        if byteval is None:
            return None

        return json.loads(byteval.decode())

    def type(self, key, path='.'):
        """
        Retrieve type of the value stored at the given path.

        Positional Arguments
        key -- The key to access

        Keyword Arguments
        path -- The path to retrieve the type of the value from.
        """
        if not isinstance(key, str):
            raise nova.exceptions.ParameterError('The provided key is not a string.')

        if not isinstance(path, str):
            raise nova.exceptions.ParameterError('The provided path is not a string.')

        try:
            byteval = self._client.execute_command('JSON.TYPE', key, path)
        except redis.exceptions.RedisError:
            raise nova.exceptions.RedisError('Could not retrieve the type for the key and path provided.')

        if byteval is None:
            return None

        val = byteval.decode()
        if val == 'integer':
            return 'number'
        if val == 'array':
            return 'list'
        if val == 'object':
            return 'dictionary'
        else:
            return val

    def keys(self, key, path='.'):
        """
        Retrieve a list of keys under the given path.

        Positional Arguments
        key -- The key to access

        Keyword Arguments
        path -- The path to retrieve the list of keys
        """
        if not isinstance(key, str):
            raise nova.exceptions.ParameterError('The provided key is not a string.')

        if not isinstance(path, str):
            raise nova.exceptions.ParameterError('The provided path is not a string.')

        # if not isinstance(self.type(key, path), dict):
        #     raise nova.exceptions.ValueError('The currently stored value at the provided key and path is not a dict.')

        try:
            data = self._client.execute_command('JSON.OBJKEYS', key, path)
        except (redis.exceptions.RedisError, redis.exceptions.ResponseError):
            raise nova.exceptions.RedisError('Could not retrieve the keys for the provided key and path.')

        return_value = []
        for entry in data:
            return_value.append(entry.decode())

        return return_value

    def delete(self, key, path='.'):
        """
        Remove a given path.

        Positional Arguments
        key -- The key to remove from

        Keyword Arguments
        path -- The path to remove
        """
        if not isinstance(key, str):
            raise nova.exceptions.ParameterError('The provided key is not a string.')

        if not isinstance(path, str):
            raise nova.exceptions.ParameterError('The provided path is not a string.')

        try:
            self._client.execute_command('JSON.DEL', key, path)
        except redis.exceptions.RedisError:
            raise nova.excpetions.RedisError('Could not remove the specified key and path.')

    def drop_all_keys(self):
        """
        Removes all keys from the database. Please use with utmost care as this can not be undone!
        """

        keys = self._client.execute_command('SCAN 0')
        # delete_keys = ' '.join(keys[1])
        delete_keys = ''
        for key in keys[1]:
            delete_keys += key.decode() + ' '

        self._client.execute_command('DEL ' + delete_keys)
