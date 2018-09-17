import json
import unittest
import nova.connector
import redis
import nova.exceptions


class ConnectorTest(unittest.TestCase):
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

        self._connector = nova.connector.Connection(host='127.0.0.1', port=6379, db=1)

    def test_set(self):
        with self.assertRaises(nova.exceptions.ParameterError):
            self._connector.set(1230, {})
            self._connector.set('__unittest', {}, 10)

        with self.assertRaises(nova.exceptions.RedisError):
            self._connector.set('somekeythatdoesntexist', {}, '.test')
            self._connector.set('__unittest', {}, 'some.path')

        try:
            self._connector.set('__unittest', 'set_test', '.set_test')
            self._connector.set('__unittest', 'set_test', 'set_test')
        except Exception as e:
            self.fail('Failed to set the value. The following error was thrown: ' + e)

    def test_get(self):
        with self.assertRaises(nova.exceptions.ParameterError):
            self._connector.get(1230)
            self._connector.get('__unittest', 10)

        self.assertDictEqual(self._test_data, self._connector.get('__unittest'))
        self.assertIsNone(self._connector.get('__unittest', 'undefined_path.test'))
        self.assertIsNone(self._connector.get('somekeythatisnotdefined'))

    def test_type(self):
        with self.assertRaises(nova.exceptions.ParameterError):
            self._connector.type(1230)
            self._connector.type('__unittest', 10)

        self.assertIsNone(self._connector.type('__unittest', 'undefined_path'))
        self.assertIsNone(self._connector.type('somekeythatisnotdefined'))

        self.assertEqual('string', self._connector.type('__unittest', 'string'))
        self.assertEqual('number', self._connector.type('__unittest', 'number'))
        self.assertEqual('list', self._connector.type('__unittest', 'list'))
        self.assertEqual('dictionary', self._connector.type('__unittest', 'dictionary'))

    def test_keys(self):
        with self.assertRaises(nova.exceptions.ParameterError):
            self._connector.keys(1230)
            self._connector.keys('__unittest', 10)

        self.assertListEqual(['string', 'number', 'boolean', 'list', 'dictionary'], self._connector.keys('__unittest'))

        with self.assertRaises(nova.exceptions.RedisError):
            self._connector.keys('__unittest', 'string')
            self._connector.keys('__unittest', 'list')
            self._connector.keys('__unittest', 'number')
            self._connector.keys('__unittest', 'boolean')

    def test_delete(self):
        with self.assertRaises(nova.exceptions.ParameterError):
            self._connector.delete(1230)
            self._connector.delete('__unittest', 10)

        self._connector.delete('__unittest', 'boolean')
        self.assertIsNone(self._connector.get('__unittest', 'boolean'))

    def test_drop_all_keys(self):
        self._connector.drop_all_keys()
        self.assertIsNone(self._connector.get('__unittest'))
