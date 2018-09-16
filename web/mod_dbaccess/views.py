import flask
import re
import json

import nova.exceptions

import nova.user
import nova.accessor
from web.utils import build_response
from config.database import DB_STRUCTURE, DB_ROLES


class Views(object):
    def __init__(self):
        self._accessor = nova.accessor.Accessor()

    def dbaccess(self, path):
        if path.startswith('/'):
            path = path[1:]

        path = path.replace('/', '.')
        root = path.split('.')[0]

        if root not in DB_STRUCTURE:
            return self._error_response('RootNotFound', 'Could not find the requested root node for the path "' + path + '".', 404)

        if flask.request.method == 'GET':
            return self._build_get_response(path, DB_STRUCTURE[root])
        elif flask.request.method == 'POST':
            return self._build_post_response(path, DB_STRUCTURE[root])
        elif flask.request.method == 'DELETE':
            return self._build_delete_response(path, DB_STRUCTURE[root])
        else:
            return self._error_response('MethodNotAllowed', 'Only GET, POST and DELETE are supported by the API', 405)

    def _error_response(self, name, message, code,  headers=[]):
        data = {
            'error': code,
            'name': name,
            'message': message
        }

        return self._response(data, code, headers)

    def _response(self, data, code, headers=[]):
        return build_response(data, code, headers + [('Content-Type', 'application/json')])

    def _retrieve_auth(self):
        return flask.request.authorization

    def _retrieve_user(self, email, password):
        user = nova.user.User(email=email)
        if not user.password_valid(password):
            return None

        return user

    def _build_get_response(self, path, permissions):
        if permissions[0] == 'private' or permissions[0] == 'shared':
            auth = self._retrieve_auth()
            if auth is None:
                return self._error_response('MissingAuthorization', 'The authorization header is missing', 400)

            user = self._retrieve_user(auth.username, auth.password)
            if user is None:
                return self._error_response('InvalidCredentials', 'The provided credentials could not be verified.', 401)

            try:
                data = self._accessor.get(path, encrypted=True, password=auth.password)
            except (nova.exceptions.ParameterError, nova.exceptions.ValueError) as e:
                return self._error_response('ParameterError', 'Something went wrong with the parameters. Please try again and contact an administrator if the problem persists.', 400)
            except nova.exceptions.PermissionError as e:
                return self._error_response('InsufficientPermissions', 'This user does not have access to the resource.', 403)
            except nova.exceptions.DecryptionError as e:
                return self._error_response('DecryptionError', 'Something went wrong when trying to decrypt the message. Please try again and contact an administrator if the problem persists.', 500)
        else:
            data = self._accessor.get(path)

        return self._response(data, 200)

    def _build_delete_response(self, path, permissions):
        auth = self._retrieve_auth()
        if auth is None:
            return self._error_response('MissingAuthorization', 'The authorization header is missing.', 400)

        user = self._retrieve_user(auth.username, auth.password)
        if user is None:
            return self._error_response('InvalidCredentials', 'The provided credentials could not be verified.', 401)

        if not self._get_user_access(path, user, permissions[1]):
            return self._error_response('InsufficientPermissions', 'The provided user does not have access to edit this resource.', 403)

        try:
            self._delete_data(path, user, permissions[0])
        except nova.exceptions.ParameterError as e:
            return self._error_response('DataError', e.message, 400)
        except nova.exceptions.DatabaseWriteError as e:
            return self._error_response('DatabaseWriteError', e.message, 500)
        except nova.exceptions.EncryptionError as e:
            return self._error_response('EncryptionError', e.message, 500)
        except nova.exceptions.PermissionError as e:
            return self._error_response('PermissionError', e.message, 500)

    def _build_post_response(self, path, permissions):
        auth = self._retrieve_auth()
        if auth is None:
            return self._error_response('MissingAuthorization', 'The authorization header is missing.', 400)

        user = self._retrieve_user(auth.username, auth.password)
        if user is None:
            return self._error_response('InvalidCredentials', 'The provided credentials could not be verified.', 401)

        if not self._get_user_access(path, user, permissions[1]):
            return self._error_response('InsufficientPermissions', 'The provided user does not have access to edit this resource.', 403)

        print(json.loads(flask.request.data))
        data = flask.request.get_json(silent=True)
        if data is None:
            return self._error_response('DataError', 'The provided data could not be parsed and is probably not correctly formatted JSON.', 400)
        if 'data' not in data:
            return self._error_response('DataError', 'The provided data does not contain a "data" object with data to be set.', 400)

        try:
            self._post_data(path, data, permissions[0], auth.password, user.fingerprint)
        except nova.exceptions.ParameterError as e:
            return self._error_response('DataError', e.message, 400)
        except nova.exceptions.DatabaseWriteError as e:
            return self._error_response('DatabaseWriteError', e.message, 500)
        except nova.exceptions.EncryptionError as e:
            return self._error_response('EncryptionError', e.message, 500)
        except nova.exceptions.PermissionError as e:
            return self._error_response('PermissionError', e.message, 500)

        return self._build_get_response(path, permissions)

    def _post_data(self, path, data, space, password, fingerprint=''):
        if space == 'private' or space == 'shared':
            if space == 'private':
                recipients = [fingerprint]
            else:
                recipients = data['recipients']

            self._accessor.set(path, data['data'], encrypted=True, password=password, recipients=recipients)
        else:
            self._accessor.set(path, data['data'])

    def _delete_data(self, path, space):
        if space == 'private' or space == 'shared':
            self._accessor.delete(path)

    def _get_user_access(self, path, user, path_role):
        if 'userid_' in path:
            userids = re.findall(r'(userid_\w+)', path)
            if user.userid in userids:
                return True

        if DB_ROLES.index(user.role) <= DB_ROLES.index(path_role):
            return True

        return False
