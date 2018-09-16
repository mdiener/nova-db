import os
import argparse
import textwrap
import getpass
import json
import hjson
import nova.manager
import nova.exceptions
import nova.connector


manager = nova.manager.Manager()


def _list_users():
    userlist = manager.get_all_users()
    print(json.dumps(userlist, sort_keys=True, indent=4))


def _show_user(userid):
    user = manager.get_user(userid=userid)
    print('userid:          ' + user['userid'])
    print('email:           ' + user['email'])
    print('hashed_password: ' + user['hashed_password'])
    print('role:            ' + user['role'])
    print('salt:            ' + user['salt'])


def _create_user(additional_args):
    print(additional_args)
    if len(additional_args) > 0:
        email = additional_args[0]
    else:
        email = input('Email: ')

    if len(additional_args) > 1:
        role = additional_args[1]
    else:
        role = input('Role: ')

    if len(additional_args) > 2:
        password = additional_args[2]
    else:
        password = getpass.getpass()

    userid = manager.create_user(email, password, role)
    print('Created the new user:\n')
    _show_user(userid)


def _edit_user(userid, current_password, edit_args):
    if len(edit_args) < 1:
        edit_cmd = input('What would you like to edit: role, password or verify: ')
    else:
        edit_cmd = edit_args[0]
        edit_args = edit_args[1:]

    if edit_cmd == 'role':
        if len(edit_args) < 1:
            role = input('Specify the new role for this user: ')
        else:
            role = edit_args[0]

        manager.set_role(userid, role)
    elif edit_cmd == 'password':
        if len(edit_args) < 1:
            new_password = getpass.getpass(prompt='Provide the new password for the user: ')
            new_password_confirm = getpass.getpass(prompt='Confirm the new password: ')
            if new_password != new_password_confirm:
                raise nova.exceptions.CMDLineError('Your new passwords do not match. Please try again.')
        else:
            new_password = edit_args[1]

        manager.update_password(userid, current_password, new_password)
    elif edit_cmd == 'verify':
        manager.verify(userid)
    else:
        raise nova.exceptions.CMDLineError('The edit user command you specified is not understood. Possible commands are: password, role, verify.')

    print('Edited user:\n')
    _show_user(userid)


def _delete_user(userid):
    manager.delete_user(userid)
    print('Removed user')


def _list_roots():
    roots = manager.get_all_root_nodes()
    print(json.dumps(roots, sort_keys=True, indent=4))


def _create_root(args):
    if len(args) < 3:
        raise nova.exceptions.CMDLineError('You need to provide name, space and role to create a new root node.')

    manager.create_root_node(args[0], args[1], args[2])
    print('Root node created.\n')
    _list_roots()


def _edit_root(rootname, args):
    if len(args) < 2:
        raise nova.exceptions.CMDLineError('You need to provide space and role when editing a root node.')

    manager.edit_root_node(rootname, args[0], args[1])
    print('Root node edited.\n')
    _list_roots()


def _delete_root(rootname):
    manager.delete_root_node(rootname)
    print('Root node deleted.\n')
    _list_roots()


def _show_node(rootname, userid, password, args):
    if len(args) < 1:
        raise nova.exceptions.CMDLineError('You need to provide the path to the node you wish to access. To access data under a root node provide "." as the path.')

    roots = manager.get_all_root_nodes()
    if rootname not in roots:
        raise nova.exceptions.CMDLineError('The provided root name is not an existing root.')

    if args[0].startswith('.'):
        path = rootname + args[0]
    else:
        path = rootname + '.' + args[0]

    root = roots[rootname]
    if root['space'] == 'shared' or root['space'] == 'private':
        if userid is None or password is None:
            raise nova.exceptions.CMDLineError('You need to provide the password and userid to access a private or shared resource.')

        data = manager.get_accessor().get(path, encrypted=True, userid=userid, password=password)
    else:
        data = manager.get_accessor().get(path)

    print(json.dumps(data, sort_keys=True, indent=4))


def _edit_node(rootname, recipients, password, args):
    if len(args) < 2:
        raise nova.exceptions.CMDLineError('You need to provide the path and the data you want to set.')

    roots = manager.get_all_root_nodes()
    if rootname not in roots:
        raise nova.exceptions.CMDLineError('The provided root name is not an existing root.')

    data = json.loads(args[1])
    if args[0].startswith('.'):
        path = rootname + args[0]
    else:
        path = rootname + '.' + args[0]

    root = roots[rootname]
    if root['space'] == 'shared' or root['space'] == 'private':
        if recipients is None or password is None:
            raise nova.exceptions.CMDLineError('You need to provide the password and userid to access a private node.')

        if root['space'] == 'private':
            recipients = [recipients]
        if root['space'] == 'shared':
            recipients = recipients.split(';')

        manager.get_accessor().set(path, data, encrypted=True, recipients=recipients, password=password)
    else:
        manager.get_accessor().set(path, data)

    _show_node(rootname, recipients, password, [args[0]])


def _delete_node(rootname, recipients, password, args):
    roots = manager.get_all_root_nodes()
    if rootname not in roots:
        raise nova.exceptions.CMDLineError('The provided root name is not an existing root.')

    if root['space'] == 'private' or root['space'] == 'shared':
        if recipients is None or password is None:
            raise nova.exceptions.CMDLineError('You need to provide the password and userid to access a private node.')

        if root['space'] == 'private':
            recipients = [recipients]
        if root['space'] == 'shared':
            recipients = recipients.split(';')

        manager.get_accessor().remove(rootname + '.' + args[0], encrypted=True, recipients=recipients, password=password)
    else:
        manager.get_accessor().remove(rootname + '.' + args[0])


def _show_roles():
    roles = manager.get_all_roles()
    rolestring = ''

    for role in roles:
        rolestring += role + ' > '

    rolestring = rolestring[:-3]
    print(rolestring)


def _update_roles(roles):
    manager.update_roles(roles)
    _show_roles()


def _load_database(args):
    if len(args) < 1:
        raise nova.exceptions.CMDLineError('You need to provide a file from which to load the base values from.')
    json_file_path = args[0]

    if not os.path.exists(json_file_path):
        raise nova.exceptions.CMDLineError('The provided path to the file does not exist.')

    with open(json_file_path, 'r') as f:
        text = f.read()

    try:
        data = hjson.loads(text)
    except hjson.scanner.HjsonDecodeError as e:
        raise nova.exceptions.CMDLineError('Could not parse the config file. Following error was thrown:\n' + e.msg + ' on line ' + str(e.lineno) + ' column ' + str(e.colno))

    confirmation = input('Continuing with this operation will wipe all data from the database. Do you want to continue: [y/N] ')
    if confirmation != 'y':
        print('Aborting ... No action taken.')
        return

    c = nova.connector.Connection()
    c.drop_all_keys()

    manager.get_accessor().set('_config', {})
    manager.get_accessor().set('_users', {})
    manager.get_accessor().set('_verify_email', {})

    if 'roles' in data:
        manager.update_roles(data['roles'])
    if 'roots' in data:
        for key, value in data['roots'].items():
            manager.create_root_node(key, value[0], value[1])
    if 'presets' in data:
        for root, preset in data['presets'].items():
            for path, data in preset.items():
                manager.get_accessor().set(root + '.' + path, data)

    print('Database set to default values.')


def _process_args(args, rootname, userid, recipients, password):
    cmd = args[0]
    additional_args = args[1:]

    if cmd == 'list-users':
        print('Listing Users ...\n')
        _list_users()
    elif cmd == 'show-user':
        print('Showing details for one user ...\n')
        if userid is None:
            raise nova.exceptions.CMDLineError('You need to specify which user you would like to show by adding --user [userid] to the command.')
        _show_user(userid)
    elif cmd == 'create-user':
        print('Creating a new user ...\n')
        _create_user(additional_args)
    elif cmd == 'edit-user':
        print('Editing a user ...\n')
        if userid is None:
            raise nova.exceptions.CMDLineError('You need to specify which user you would like to edit by adding --user [userid] to the command.')
        if len(additional_args) > 0 and additional_args[0] == 'password' and password is None:
            raise nova.exceptions.CMDLineError('You need to provide the current password if you want to change a user\'s password.')
        _edit_user(userid, password, additional_args)
    elif cmd == 'delete-user':
        print('Deleting user ...\n')
        if userid is None:
            raise nova.exceptions.CMDLineError('You need to specify which user you would like to edit by adding --user [userid] to the command.')
        _delete_user(userid)
    elif cmd == 'list-roots':
        print('Listing roots ...\n')
        _list_roots()
    elif cmd == 'create-root':
        print('Creating root ...\n')
        _create_root(additional_args)
    elif cmd == 'edit-root':
        print('Editing root ...\n')
        if rootname is None:
            raise nova.exceptions.CMDLineError('You need to specify which root node you would like to edit.')
        _edit_root(rootname, additional_args)
    elif cmd == 'delete-root':
        print('Deleting root ...\n')
        if rootname is None:
            raise nova.exceptions.CMDLineError('You need to specify which root node you would like to delete.')
        _delete_root(rootname, additional_args)
    elif cmd == 'show-node':
        print('Showing node ...\n')
        if rootname is None:
            raise nova.exceptions.CMDLineError('You need to specify the root node under which the data you tried to access resides.')
        _show_node(rootname, userid, password, additional_args)
    elif cmd == 'edit-node':
        print('Editing node ...\n')
        _edit_node(rootname, recipients, password, additional_args)
    elif cmd == 'delete-node':
        print('Deleting node ...\n')
        _delete_node(rootname, recipients, password, additional_args)
    elif cmd == 'show-roles':
        print('Showing roles ...\n')
        _show_roles()
    elif cmd == 'update-roles':
        print('Updating roles ...\n')
        _update_roles(additional_args)
    elif cmd == 'load':
        _load_database(additional_args)
    else:
        print('Command not recognized!')

    print('\n')

def _get_description():
    return '''\
Manage your running NOVA instance.'''


def _get_epilog():
        return '''\
Commands
-------------
The following commands can be supplied to manage NOVA.
    list-users      Lists all users in your nova instance.
                    Ex.: python manage.py list-users

    show-user       Show details about a single user. --user (-u) is required with this command.
                    Ex.: python manage.py show-user --user [userid]

    create-user     Create a new user.
                    Ex.: python manage.py create-user [email (optional)] [role (optional)] [password (optional)]

    edit-user       Change user settings. Settings that can be changed: role, verified,
                    password (requires old password). --user (-u) is required with this command.
                    Ex.: python manage.py edit-user [role] [newrole] --user [userid]
                         python manage.py edit-user [password] [new_password] --user [userid] --password [password]
                         python manage.py edit-user [verify] --user [userid]

    delete-user     Remove a user.
                    Ex.: python manage.py delete-user --user [userid]

    list-roots      Lists all the root nodes defined. (Excluding internal ones.)
                    Ex.: python manage.py list-roots

    create-root     Create a new root node.
                    Ex.: python manage.py create-root [rootname] [root_space] [root_role]

    edit-root       Edit a root node.
                    Ex.: python manage.py edit-root [root_space] [root_role] --root [rootname]

    delete-root     Delete a root node.
                    Ex.: python manage.py delete-root --root [rootname]

    show-node       Show the node. --root (-r) is required with this command. If you try to
                    access a node that is under a private or shared root you need to specify the password and userid
                    of the user owning that requested node.
                    Ex.: python manage.py show-node [.path.to.the.node] --root [rootname] --user [userid] --password [password]

    edit-node       Edit an existing node. --root (-r) is required with this command. If you try to
                    set a node that is on a private root you will need to provide your userid with --recipients and your password.
                    If you want to set a node that is on a shared root you will need to provide the userid of all recipients and your personal password.
                    Please make sure you enclose your data in single quotes or it will fail.
                    Ex.: python manage.py edit-node [.path.to.the.node] 'data' --root [rootname] --recipients [userid;userid;userid] --password [password]

    delete-node     Delete an existing node. --root (-r) is required with thid command.
                    Ex.: python manage.py delete-node [.path.to.the.node] --root [rootname]

    show-roles      Show the currently set role config.
                    Ex.: python manage.py show-roles

    update-roles    Sets the roles available for all users. The first and last role need to be 'admin' or 'user' (you
                    can ommit them and they will be added automatically).
                    Ex.: python manage.py update-roles [admin moderator user]

    load            Load the database with the base values specified by the file. This will wipe the
                    database and set it to values defined in the file specified.
                    See the profided default.json for details on values that can be set.
                    Ex.: python manage.py initialize [path/to/startvalues.json]
'''


parser = argparse.ArgumentParser(description=textwrap.dedent(_get_description()), epilog=textwrap.dedent(_get_epilog()), formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('cmd', nargs='*', action='store', help='Execute the given command.')
parser.add_argument('--user', '-u', action='store', help='Specify the user for the command to be executed on.')
parser.add_argument('--password', '-p', action='store', help='Specify the password to use with the command.')
parser.add_argument('--root', '-r', action='store', help='Specify the root node for the command to be executed on.')
parser.add_argument('--recipients', action='store', help='List the recipients as userids for all the users needing access to this resource.')

args = parser.parse_args()

try:
    _process_args(args.cmd, args.root, args.user, args.recipients, args.password)
except nova.exceptions.CMDLineError as e:
    print(e)
