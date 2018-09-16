import nova.accessor
import nova.exceptions


class Config(object):
    def __init__(self):
        self._accessor = nova.accessor.Accessor()

        if not self._accessor.exists('_config'):
            self._accessor.set('_config', {})

    def get_roots(self):
        roots = self._accessor.get('_config.roots')
        if roots is None:
            return []
        return roots

    def add_root(self, name, space, role):
        if not isinstance(name, str) or not isinstance(space, str) or not isinstance(role, str):
            raise nova.exceptions.ParameterError('The provided root name, space or role are not strings.')

        if not self._accessor.exists('_config.roots'):
            self._accessor.set('_config.roots', {})

        self._accessor.set('_config.roots.' + name, {
            'space': space,
            'role': role
        })

    def remove_root(self, name):
        self._accessor.remove('_config.roots.' + name)

    def get_roles(self):
        roles = self._accessor.get('_config.roles')
        if roles is None:
            return []
        return roles

    def update_roles(self, role_list):
        if not isinstance(role_list, list):
            raise nova.exceptions.ParameterError('The provided role_list is not a list of roles.')

        if 'admin' in role_list:
            if role_list.index('admin') != 0:
                raise nova.exceptions.ParameterError('The role "admin" needs to be at position 0 in the role list.')

        if 'user' in role_list:
            if role_list.index('user') != len(role_list) - 1:
                raise nova.exceptions.ParameterError('The role "user" needs to be at the last position in the role list.')

        if role_list[0] != 'admin':
            role_list = ['admin'] + role_list
        if role_list[-1] != 'user':
            role_list = role_list + ['user']

        if not self._accessor.exists('_config.roles'):
            self._accessor.set('_config.roles', {})

        self._accessor.set('_config.roles', role_list)
