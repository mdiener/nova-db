import hashlib

import nova.user
import nova.exceptions
import nova.config
import nova.accessor


class Manager(object):
    def __init__(self):
        self._accessor = nova.accessor.Accessor()
        self._config = nova.config.Config()

    def get_accessor(self):
        return self._accessor

    def get_all_root_nodes(self):
        return self._config.get_roots()

    def create_root_node(self, root_name, root_space, root_role):
        if not isinstance(root_name, str) or not isinstance(root_space, str) or not isinstance(root_role, str):
            raise nova.exceptions.ParameterError('The provided root_name, root_space and/or root_role are not strings.')

        spaces = ['private', 'shared', 'protected', 'public']
        if root_space not in spaces:
            raise nova.exceptions.ParameterError('The provided space for the node is not private, shared, protected or public.')
        if root_role not in self._config.get_roles():
            raise nova.exceptions.ParameterError('The provided roles for the root node is not in the approved roles ' + ' '.join(self._config.get_roles()) + '.')
        if root_name in self._config.get_roots():
            raise nova.exceptions.ParameterError('The provided root already exists. If you want to change a root please use the edit_root_node function.')

        self._config.add_root(root_name, root_space, root_role)
        self._accessor.set(root_name, {})

    def edit_root_node(self, root_name, root_space=None, root_role=None):
        if not isinstance(root_name, str) or not isinstance(root_space, str) or not isinstance(root_role, str):
            raise nova.exceptions.ParameterError('The provided root_name, root_space and/or root_role are not strings.')

        if root_name not in self._config.get_roots():
            raise nova.exceptions.ParameterError('The provided root does not exist.')

        current_root = self._config.get_roots()[root_name]

        if root_space is not None:
            if root_space == 'shared' or root_space == 'private':
                raise nova.exceptions.NovaError('You can change a node to private or shared after its creation.')

            if current_root['space'] == 'shared' or current_root['space'] == 'private':
                raise nova.exceptions.NovaError('You can not change a private or shared root\'s space.')
        else:
            root_space = current_root['space']

        if root_role is not None:
            if root_role not in self._config.get_roles():
                raise nova.exceptions.ParameterError('The provided role is not defined as a role.')
        else:
            root_role = current_root['role']

        self._config.add_root(root_name, root_space, root_role)

    def delete_root_node(self, root_name):
        if not isinstance(root_name, str):
            raise nova.exceptions.ParameterError('The provided root node is not a string.')

        if root_name not in self._config.get_roots():
            raise nova.exceptions.ParameterError('The provided root does not exist.')

        self._config.remove_root(root_name)
        self._accessor.remove(root_name)

    def get_all_users(self):
        users = self._accessor.get('_users.')
        user_list = []

        if users is not None:
            for userid, user in users.items():
                user_list.append({
                    'userid': userid,
                    'email': user['email']
                })

        return user_list

    def create_user(self, email, password, role='user'):
        if not isinstance(email, str) or not isinstance(password, str) or not isinstance(role, str):
            raise nova.exceptions.ManagerError('Both the email and password need to be a string.')

        password = hashlib.sha512(password.encode()).hexdigest()

        user = nova.user.User()
        try:
            user.create(email, password, role)
        except nova.exceptions.UserExistsError as e:
            print('The user with email "' + email + '" existed already and has not been modified.')
        except nova.exceptions.NovaError as e:
            raise nova.exceptions.ManagerError('Could not create the admin user "' + email + '".')

        return user.userid

    def get_user(self, **kwargs):
        userid = None
        email = None

        if kwargs is not None:
            if 'userid' in kwargs:
                userid = kwargs['userid']
            elif 'email' in kwargs:
                email = kwargs['email']
            else:
                raise nova.exceptions.ParameterError('You need to provide either userid or email as keyword arguments.')

        if userid is not None:
            user = nova.user.User(userid=userid)
        else:
            user = nova.user.User(email=email)

        return {
            'userid': user.userid,
            'email': user.email,
            'role': user.role,
            'salt': user.salt,
            'hashed_password': user.hashed_password
        }

    def edit_user(self, userid, task, **kwargs):
        if not isinstance(userid, str):
            raise nova.exceptions.ParameterError('The provided userid is not a string.')
        if not isinstance(task, str) and task not in ['edit_pass', 'edit_role', 'verify']:
            raise nova.exceptions.ParameterError('The provided task is not "edit_pass", "edit_role" or "verify".')

        user = nova.user.User(userid=userid)

        if task == 'verify':
            user.verify(None, True)
        if task == 'edit_pass':
            if 'old_password' not in kwargs or 'new_password' not in kwargs:
                raise nova.exceptions.ParameterError('To change a user\'s password the old_password and new_password kwargs have to be set.')
            user.edit_password(kwargs['old_password'], kwargs['new_password'])
        if task == 'edit_role':
            if 'new_role' not in kwargs:
                raise nova.exceptions.ParameterError('To change a user\'s role the new_role kwarg has to be set.')
            user.edit_role(kwargs['role'])

    def delete_user(self, userid):
        user = nova.user.User(userid=userid)
        user.delete()

    def get_all_roles(self):
        return self._config.get_roles()

    def update_roles(self, roles):
        if not isinstance(roles, list):
            raise nova.exceptions.ParameterError('The provided roles is not a list of roles.')

        self._config.update_roles(roles)
