import json
import unittest
import nova.accessor
import redis
import nova.exceptions


class AccessorTest(unittest.TestCase):
    def setUp(self):
        self._test_data = {
            'string': 'foobar',
            'number': 10.4,
            'boolean': True,
            'list': [1, 2, 3],
            'dictionary': {'one': 'two'}
        }

        redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)
        redis_client.execute_command('DEL __unittest')
        redis_client.execute_command('JSON.SET', '__unittest', '.', '{}')
        redis_client.execute_command('JSON.SET', '__unittest', '.', json.dumps(self._test_data))

        self._accessor = nova.accessor.Accessor(host='127.0.0.1', port=6379, db=1)

    def test_exists(self):
        self.assertIsTrue(self._accessor.exists('__unittest.number'))
