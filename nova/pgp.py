"""GPG Support Module."""

import pgpy
import nova.connector
import nova.exceptions


class OpenPGP(object):
    """
    OpenPGP Encryption and Decryption Helper Class.

    Storage and usage helper for openpgp keys. You can create new keys, encrypt
    and decrypt data with a key and delete a key you previously created.
    """

    def __init__(self):
        self._connector = nova.connector.Connection()
        if self._connector.get('_keys') is None:
            self._connector.set('_keys', {})

    def create_key(self, userid, email, password):
        key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 4096)
        uid = pgpy.PGPUID.new('NOVA ' + email, comment='Generated using NOVA', email=email)
        key.add_uid(
            uid,
            usage={pgpy.constants.KeyFlags.Sign, pgpy.constants.KeyFlags.EncryptCommunications, pgpy.constants.KeyFlags.EncryptStorage},
            hashes=[pgpy.constants.HashAlgorithm.SHA256, pgpy.constants.HashAlgorithm.SHA384, pgpy.constants.HashAlgorithm.SHA512, pgpy.constants.HashAlgorithm.SHA224],
            ciphers=[pgpy.constants.SymmetricKeyAlgorithm.AES256, pgpy.constants.SymmetricKeyAlgorithm.AES192, pgpy.constants.SymmetricKeyAlgorithm.AES128],
            compression=[pgpy.constants.CompressionAlgorithm.ZLIB, pgpy.constants.CompressionAlgorithm.BZ2, pgpy.constants.CompressionAlgorithm.ZIP, pgpy.constants.CompressionAlgorithm.Uncompressed]
        )
        key.protect(password, pgpy.constants.SymmetricKeyAlgorithm.AES256, pgpy.constants.HashAlgorithm.SHA256)

        self._connector.set('_keys', str(key), '.'+userid)

    def encrypt(self, message, userids):
        if not isinstance(message, str):
            raise nova.exceptions.ParameterError('The provided message is not a string.')

        if isinstance(userids, str):
            userids = [userids]
        else:
            if not isinstance(userids, list):
                raise nova.exceptions.ParameterError('The provided userids has to be either a list of strings or a string.')

        keys = []
        for userid in userids:
            keytext = self._connector.get('_keys', '.'+userid)
            k = pgpy.PGPKey()
            k.parse(keytext)
            keys.append(k)

        pgp_msg = pgpy.PGPMessage.new(message)
        cipher = pgpy.constants.SymmetricKeyAlgorithm.AES256
        sessionkey = cipher.gen_key()

        enc_msg = keys[0].encrypt(pgp_msg, cipher=cipher, sessionkey=sessionkey)
        for key in keys:
            enc_msg = key.encrypt(enc_msg, cipher=cipher, sessionkey=sessionkey)

        del sessionkey

        return str(enc_msg)

    def decrypt(self, message, userid, password):
        if not isinstance(message, str):
            raise nova.exceptions.ParameterError('The provided message is not a string.')
        if not isinstance(userid, str):
            raise nova.exceptions.ParameterError('The provided userid is not a string.')
        if not isinstance(password, str):
            raise nova.exceptions.ParameterError('The provided password is not a string.')

        key = self._get_key(userid)

        enc_msg = pgpy.PGPMessage.from_blob(message)

        try:
            with key.unlock(password):
                pgp_msg = key.decrypt(enc_msg)
        except pgpy.PGPDecryptionError as e:
            raise nova.exceptions.DecryptionError('Could not decrypt the message with the provided password.')

        return pgp_msg.message

    def delete_key(self, userid):
        if not isinstance(userid, str):
            raise nova.exception.ParameterError('The provided userid is not a string.')

        self._connector.delete('_keys', '.' + userid)

    def update_password(self, userid, old_password, new_password):
        if not isinstance(userid, str):
            raise nova.exception.ParameterError('The provided userid is not a string.')
        if not isinstance(old_password, str):
            raise nova.exceptions.ParameterError('The provided password is not a string.')
        if not isinstance(new_password, str):
            raise nova.exceptions.ParameterError('The provided new password is not a string.')

        key = self._get_key(userid)
        try:
            key.unlock(old_password)
        except pgpy.PGPDecryptionError as e:
            raise nova.exceptions.KeyUnlockError('Could not unlock the key with the provided password.')

        key.protect(new_password, pgpy.constants.SymmetricKeyAlgorithm.AES256, pgpy.constants.HashAlgorithm.SHA256)

        self._connector.set('_keys', str(key), '.'+userid)

    def _get_key(self, userid):
        key_str = self._connector.get('_keys', '.'+userid)
        key = pgpy.PGPKey()
        key.parse(key_str)

        return key
