#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: adminuser

short_description: Manage admin user

description: Manage SmartZone admin users.

options:
    name:
        description: Name of the admin user.
        required: True
        type: str
    realName:
        description: Relanme of the admin user.
        type: str
    phone:
        description: Relanme of the admin user.
        type: str
    email:
        description: Email address of the admin user.
        type: str
    title:
        description: Email address of the admin user.
        type: str
    password:
        description: Initial password of the admin user.
        type: str
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        realName=dict(type='str'),
        phone=dict(type='str'),
        email=dict(type='str'),
        title=dict(type='str'),
        password=dict(type='str', no_log=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    state = module.params.get('state')
    password = module.params.get('password')

    # Get current user
    query = dict(
        fullTextSearch=dict(
            type="OR",
            value=name,
            fields=["userName"]
        )
    )
    users = conn.post('users/query', payload=query, expected_code=200)
    current_user = None
    for user in users['list']:
        if user['userName'] == name:
            current_user = user
            result['user'] = user

    # Create
    if current_user is None and state == 'present':
        result['changed'] = True
        new_user = dict(
            userName=name,
            newPassphrase=password,
        )
        for key in ['realName', 'phone', 'email', 'title']:
            value = module.params.get(key)
            if not value:
                continue
            new_user[key] = value
        if not module.check_mode:
            resp = conn.post('users', payload=new_user)
            new_user = conn.get(f"users/{resp['id']}")
        result['user'] = new_user

    # Update
    elif state == 'present':
        update_user = dict(id=current_user['id'])
        for key in ['realName', 'phone', 'email', 'title']:
            value = module.params.get(key)
            if value and user[key] != value:
                update_user[key] = value

        if len(update_user) > 1:
            result['changed'] = True
            result['update'] = update_user
            if not module.check_mode:
                conn.patch(f"users/{current_user['id']}", payload=update_user)
                new_user = conn.get(f"users/{current_user['id']}")
            else:
                new_user = copy.deepcopy(current_user)
                new_user.update(update_user)
            result['user'] = new_user

    # Delete
    elif current_user is not None and state == 'absent':
        result['changed'] = True
        new_user = None
        if not module.check_mode:
            conn.delete(f"users/{current_user['id']}")

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(before=current_user, after=new_user)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
