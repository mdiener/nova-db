import json
import unittest
import uuid
import nova.pgp
import nova.exceptions


class OpenPGPTest(unittest.TestCase):
    _connector = nova.connector.Connection()

    _userid_A = 'userid_f0a1324bfe7a41f0ac36a05cf982187a'
    _password_A = 'acc21ef11dfd40d3b65598c53b0d05dc'
    _email_A = 'test_A@example.com'
    _userid_B = 'userid_a142bbafe8a442b18a52f21080d1480b'
    _password_B = '798976a856e54082b5e2e43e550880bb'
    _email_B = 'test_B@example.com'
    _message = 'This is a test message.'

    def setUp(self):
        self._connector.delete('_keys')

    def test_create_key(self):
        pgp = nova.pgp.OpenPGP()
        pgp.create_key(self._userid_A, self._password_A, self._email_A)

        self.assertIsNotNone(self._connector.get('_keys', self._userid_A))

    def test_encrypt_decrypt(self):
        pgp = nova.pgp.OpenPGP()

        pgp.create_key(self._userid_A, self._email_A, self._password_A)
        pgp.create_key(self._userid_B, self._email_B, self._password_B)

        with self.assertRaises(nova.exceptions.ParameterError):
            pgp.encrypt(True, self._userid_A)
            pgp.encrypt(self._message, 120)

        with self.assertRaises(nova.exceptions.EncryptionError):
            pgp.encrypt(self._message, 'userid_undefined')

        encrypted_message = pgp.encrypt(self._message, self._userid_A)
        decrypted_message = pgp.decrypt(encrypted_message, self._userid_A, self._password_A)

        self.assertEqual(self._message, decrypted_message)

        with self.assertRaises(nova.exceptions.DecryptionError):
            decrypted_message = pgp.decrypt(encrypted_message, self._userid_B, self._password_B)

        encrypted_message = pgp.encrypt(self._message, [self._userid_A, self._userid_B])
        decrypted_message_A = pgp.decrypt(encrypted_message, self._userid_A, self._password_A)
        decrypted_message_B = pgp.decrypt(encrypted_message, self._userid_B, self._password_B)

        self.assertEqual(self._message, decrypted_message_A)
        self.assertEqual(self._message, decrypted_message_B)

    def test_delete_key(self):
        pgp = nova.pgp.OpenPGP()
        pgp.create_key(self._userid_A, self._email_A, self._password_A)

        with self.assertRaises(nova.exceptions.ParameterError):
            pgp.delete_key(123908)

        pgp.delete_key(self._userid_A)

        self.assertIsNone(self._connector.get('_keys', self._userid_A))

    def test_update_password(self):
        pgp = nova.pgp.OpenPGP()
        pgp.create_key(self._userid_A, self._email_A, self._password_A)

        with self.assertRaises(nova.exceptions.ParameterError):
            pgp.update_password(120931, self._password_A, self._password_B)
            pgp.update_password(self._userid_A, 8309123, self._password_B)
            pgp.update_password(self._userid_A, self._password_A, 1289379)

        encrypted_message = pgp.encrypt(self._message, self._userid_A)

        pgp.update_password(self._userid_A, self._password_A, self._password_B)

        decrypted_message = pgp.decrypt(encrypted_message, self._userid_A, self._password_B)

        self.assertEqual(self._message, decrypted_message)
