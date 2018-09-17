import json
import unittest
import uuid
import nova.pgp
import nova.exceptions


class AccessorTest(unittest.TestCase):
    def setUp(self):
        self._connector = nova.connector.Connection()
        self._connector.delete('_keys')

    def test_create_key(self):
        userid = 'userid_f0a1324bfe7a41f0ac36a05cf982187a'
        password = 'acc21ef11dfd40d3b65598c53b0d05dc'
        email = 'test@example.com'

        pgp = nova.pgp.OpenPGP()
        pgp.create_key(userid, email, password)

        self.assertIsNotNone(self._connector.get('_keys', userid))

    def test_encrypt(self):
        userid_A = 'userid_f0a1324bfe7a41f0ac36a05cf982187a'
        password_A = 'acc21ef11dfd40d3b65598c53b0d05dc'
        email_A = 'test_A@example.com'
        userid_B = 'userid_f0a1324bfe7a41f0ac36a05cf982187a'
        password_B = 'acc21ef11dfd40d3b65598c53b0d05dc'
        email_B = 'test_B@example.com'

        pgp = nova.pgp.OpenPGP()
        pgp.create_key(self._userid, self._email, self._password)

        message = 'This is a test message.'
