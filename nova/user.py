"""
Internal User Handling.

Authenticate, identify, create and delete internal users required by Nova to work.
Based on the AUTH_METHOD set in config.nova this will work slightly differently, however,
it shouldn't be exposed except in some return values having slightly different keys.
"""

import hashlib
import uuid
import re
import time

import nova.exceptions
import nova.accessor
import nova.pgp
import nova.email
import nova.config
from config.nova import REQUIRE_VERIFY_EMAIL


class User(object):
    def __init__(self, userid=None, email=None):
        self._accessor = nova.accessor.Accessor()
        self._config = nova.config.Config()

        self.email = email
        self.userid = userid

        self.hashed_password = None
        self.role = None
        self.salt = None

        if REQUIRE_VERIFY_EMAIL:
            self.verified = False
        else:
            self.verified = True

        self._load_user()

    def _load_user(self):
        if self.userid is not None:
            user = self._find_user_by_userid(self.userid)
            self.email = user['email']
        elif self.email is not None:
            userid, user = self._find_user_by_email(self.email)
            self.userid = userid
        else:
            return

        self.hashed_password = user['password']
        self.role = user['role']
        self.salt = user['salt']
        self.verified = user['verified']

    def _find_user_by_userid(self, userid):
        user = self._accessor.get('_users.' + self.userid)
        if user is not None:
            return user

        raise nova.exceptions.UserNotFoundError('The user with the userid ' + userid + ' was not found.')

    def _find_user_by_email(self, email):
        users = self._accessor.get('_users.')
        if users is not None:
            for userid, user in users.items():
                if user['email'] == email:
                    return userid, user

        raise nova.exceptions.UserNotFoundError('The user with the email ' + email + ' was not found.')

    def password_valid(self, password):
        hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
        if hashed_password == self.hashed_password:
            return True
        else:
            return False

    def create(self, email, password, role='user'):
        if not isinstance(email, str) or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            raise nova.exceptions.ParameterError('The first parameter has to be a valid email address.')

        if not isinstance(password, str) and len(password) < 6:
            raise nova.exceptions.ParameterError('The second parameter has to be a valid password (at least 6 characters long).')

        if not isinstance(role, str) and role not in self._config.get_roles():
            raise nova.exceptions.ParameterError('The role parameter has to be a valid role from config.database.DB_ROLES.')

        try:
            userid, user = self._find_user_by_email(email)

            raise nova.exceptions.UserExistsError('The user with the email "' + email + '" you tried to create already exists.')
        except nova.exceptions.UserNotFoundError as e:
            pass

        pgp = nova.pgp.OpenPGP()

        self.role = role
        self.userid = 'userid_' + uuid.uuid4().hex
        self.salt = uuid.uuid4().hex[1:9]
        self.hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
        self.email = email

        if role == 'admin':
            self.verified = True

        try:
            if not self._accessor.exists('_users'):
                self._accessor.set('_users', {})

            self._accessor.set('_users.' + self.userid, {
                'password': self.hashed_password,
                'role': self.role,
                'salt': self.salt,
                'email': self.email,
                'verified': self.verified,
                'created': int(time.time())
            })
        except (nova.exceptions.ParameterError, nova.exceptions.DatabaseWriteError) as e:
            raise nova.exceptions.DatabaseWriteError('Could not write the new user to the database.')

        pgp.create_key(self.userid, self.email, password)

    def create_verification_code(self):
        if self.email is None or self.userid is None:
            raise nova.exceptions.UserNotFoundError('No user found. Please specify email and/or userid when creating the userid object.')
        if self.verified:
            raise nova.exceptions.AlreadyVerifiedError('This user is already verified.')

        verification_code = uuid.uuid4().hex
        try:
            self._accessor.set('_verify_email.' + self.userid, {
                'email': self.email,
                'code': verification_code
            })
        except (nova.exceptions.ParameterError, nova.exceptions.DatabaseWriteError) as e:
            raise nova.exceptions.DatabaseWriteError('Could not store the verification code.')

        return verification_code

    def verify(self, verification_code, force=False):
        if not force:
            verification_data = self._accessor.get('_verify_email.' + self.userid)
            if verification_data is None:
                raise nova.exceptions.VerificationNotFoundError('Could not find vierification data for this user.')

            if verification_data['code'] == verification_code:
                self.verified = True
                self._accessor.set('_users.' + self.userid + '.verified', True)
        else:
            self.verified = True
            self._accessor.set('_users.' + self.userid + '.verified', True)

    def delete(self):
        try:
            self._accessor.remove('_users.' + self.userid)
        except (nova.exceptions.ParameterError, nova.exceptions.RedisError) as e:
            raise nova.exceptions.EditUserError('Could not remove the user.')

        pgp = nova.pgp.OpenPGP()
        pgp.delete_key(self.userid)

    def edit_role(self, new_role):
        if not isinstance(new_role, str):
            raise nova.exceptions.ParameterError('The provided role is not a string.')

        try:
            self._accessor.set('_users.' + self.userid + '.role', new_role)
        except (nova.exceptions.ParameterError, nova.exceptions.RedisError) as e:
            raise nova.exceptions.EditUserError('Changing the role failed.')

    def edit_password(self, old_password, new_password):
        if not self.password_valid(old_password):
            raise nova.exceptions.PermissionError('The provided password is not correct.')

        hashed_password = hashlib.sha512(new_password.encode('utf-8')).hexdigest()

        try:
            self._accessor.set('_users.' + self.userid + '.password', hashed_password)
        except (nova.exceptions.ParameterError, nova.exceptions.RedisError) as e:
            raise e

        try:
            pgp = nova.pgp.OpenPGP()
            pgp.update_password(self.userid, old_password, new_password)
        except (nova.exceptions.KeyUnlockError, nova.exceptions.ParameterError) as e:
            hashed_password = hashlib.sha512(old_password.encode('utf-8')).hexdigest()
            self._accessor.set('_users.' + self.userid + '.password', hashed_password)

            raise nova.exceptions.EditUserError('Changing the password failed.')
