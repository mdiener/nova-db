import uuid
import flask
from config.web import OAUTH_CLIENTS, AUTH_METHOD
from config.nova import REQUIRE_VERIFY_EMAIL
from web.mod_auth.oauth.provider import get_provider_storage, Provider
import web.mod_auth.exceptions
import nova.user
import nova.exceptions
from web.utils import build_response


class Views(object):
    def __init__(self):
        self._provider_storage = get_provider_storage()
        for client in OAUTH_CLIENTS:
            self._provider_storage.add(Provider(client[0], client[1]))

    def salt(self):
        email = flask.request.args.get('email', None)
        if email is None:
            return build_response({
                'error': 400,
                'name': 'ParameterError',
                'message': 'The email of the user needs to be provided as a parameter.'
            }, 400, [('Content-Type', 'application/json')])

        user = nova.user.User(email=email)

        if user.salt is None:
            return build_response({
                'error': 404,
                'name': 'UserNotFound',
                'message': 'Could not find the requested user\'s salt.'
            }, 404, [('Content-Type', 'application/json')])

        return build_response({
            'salt': user.salt
        }, 200, [('Content-Type', 'application/json')])

    def authenticate(self):
        if AUTH_METHOD == 'basic':
            return self._auth_basic()
        elif AUTH_METHOD == 'oauth':
            return self._auth_oauth()

    def _auth_basic(self):
        email = flask.request.form.get('email', None)
        password = flask.request.form.get('password', None)

        user = nova.user.User(email=email)
        pass_valid = user.password_valid(password)

        if pass_valid:
            return build_response({}, 200, [])
        else:
            return build_response({
                'error': 401,
                'name': 'InvalidCredentials',
                'message': 'The provided credentials could not be verified.'
            }, 401, [('Content-Type', 'application/json')])

    def _auth_oauth(self):
        grant_type = flask.request.form.get('grant_type', None)
        client_id = flask.request.form.get('client_id', None)
        client_secret = flask.request.form.get('client_secret', None)
        email = flask.request.form.get('email', None)
        password = flask.request.form.get('password', None)
        refresh_token = flask.request.form.get('refresh_token', None)

        if grant_type is None or client_id is None or client_secret is None:
            return build_response({
                'error': 'invalid_request',
                'error_description': 'grant_type, client_id and client_secret need to be defined as request parameters.'
            }, 400, [('Content-Type', 'application/json')])

        try:
            provider = self._provider_storage.get(client_id)
        except web.mod_auth.exceptions.ProviderNotDefined as e:
            return build_response({
                'error': 'invalid_client',
                'error_description': 'No client found with the provided id.'
            }, 400, [('Content-Type', 'application/json')])

        try:
            access_token, refresh_token = provider.authenticate(client_secret, grant_type, email=email, password=password, refresh_token=refresh_token)
        except web.mod_auth.exceptions.WrongClientSecret as e:
            return build_response({
                'error': 'invalid_client',
                'error_description': 'The provided client secret does not match the provided client id.'
            }, 400, [('Content-Type', 'application/json')])
        except web.mod_auth.exceptions.WrongGrantType as e:
            return build_response({
                'error': 'unsupported_grant_type',
                'error_description': 'The provided grant type is not supported.'
            }, 400, [('Content-Type', 'application/json')])
        except web.mod_auth.exceptions.UserCredentialsError as e:
            return build_response({
                'error': 'invalid_grant',
                'error_description': 'The provided user credentials do not match anything.'
            }, 400, [('Content-Type', 'application/json')])

        return build_response({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': refresh_token
        }, 200, [('Content-Type', 'application/json'), ('Cache-Control', 'no-store'), ('Pragma', 'no-cache')])

    def verify(self):
        email = flask.request.args.get('email', None)
        verification_code = flask.request.args.get('verification_code', None)

        user = nova.user.User(email=email)
        try:
            user.verify(verification_code)
        except nova.exceptions.VerificationNotFoundError as e:
            return build_response({
                'error': 404,
                'name': 'VerificationDataNotFound',
                'description': 'Could not find the verification data for this email.'
            }, 404, [{'Content-Type', 'application/json'}])

        if not user.verified:
            return build_response({
                'error': 403,
                'name': 'VerificationError',
                'description': 'Verification for user with email ' + email + ' failed.'
            }, 403, [{'Content-Type', 'application/json'}])

        return build_response({}, 200, [{'Content-Type', 'application/json'}])

    def create(self):
        email = flask.request.form.get('email', None)
        password = flask.request.form.get('password', None)

        user = nova.user.User()
        try:
            user.create(email, password)
        except nova.exceptions.ParameterError as e:
            return build_response({
                'error': 400,
                'name': 'MissingEmailOrPassword',
                'description': e.message
            }, 400, [('Content-Type', 'application/json')])

        if REQUIRE_VERIFY_EMAIL:
            verification_code = uuid.uuid4().hex

            try:
                verification_code = user.create_verification_code()
            except nova.exceptions.DatabaseWriteError as e:
                return build_response({
                    'error': 500,
                    'name': 'VerificationEmailError',
                    'description': 'Could not create the verification code for this user. Please try again.'
                }, 400, [('Content-Type', 'application/json')])

            verification_link = flask.request.url_root[:-1] + flask.url_for('auth.verify', verification_code=verification_code, email=user.email)

            novamail = nova.email.Email(user.email)
            try:
                novamail.send_verification_email(verification_link)
            except nova.exceptions.EmailConnectionFailed as e:
                return build_response({
                    'error': 500,
                    'name': 'EmailConnectionFailed',
                    'description': 'Could not connect to the internal mail delivery system.'
                }, 500, [('Content-Type', 'application/json')])

            return build_response({
                'userid': user.userid,
                'email': user.email
            }, 200, [('Content-Type', 'application/json')])
        else:
            return build_response({
                'userid': user.userid,
                'email': user.email
            }, 200, [('Content-Type', 'application/json')])

    def user_by_id(self, userid):
        try:
            user = nova.user.User(userid=userid)
            return self.user_response(user)
        except nova.exceptions.UserNotFoundError as e:
            return build_response({
                'error': 404,
                'name': 'UserNotFound',
                'description': 'Could not find the user with id "' + userid + '".'
            }, 404, [('Content-Type', 'application/json')])

    def user_by_email(self):
        email = flask.request.args.get('email', None)
        if email is None:
            return build_response({
                'error': 400,
                'name': 'MissingEmailError',
                'description': 'The email needs to be provided as a get parameter: email=...'
            }, 400, [('Content-Type', 'application/json')])

        try:
            user = nova.user.User(email=email)
            return self.user_response(user)
        except nova.exceptions.UserNotFoundError as e:
            return build_response({
                'error': 404,
                'name': 'UserNotFound',
                'description': 'Could not find the user with email "' + email + '".'
            }, 404, [('Content-Type', 'application/json')])

    def user_response(self, user):
        return build_response({
            'email': user.email,
            'fingerprint': user.fingerprint,
            'salt': user.salt,
            'role': user.role,
            'userid': user.userid,
            'verified': user.verified
        }, 200, [('Content-Type', 'application/json')])
