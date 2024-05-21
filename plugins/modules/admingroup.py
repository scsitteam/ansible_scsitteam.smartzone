#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection

def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        role=dict(type='str', choices=["SUPER_ADMIN", "SYSTEM_ADMIN", "NETWORK_ADMIN", "RO_NETWORK_ADMIN", "RO_SYSTEM_ADMIN", "AP_ADMIN", "GUEST_PASS_ADMIN", "MVNO_SUPER_ADMIN"]),
        accountSecurityProfile=dict(type='str', default='Default'),
        permissions=dict(type='list', options=dict(
            resource=dict(type='str', required=True),
            access=dict(type='str', choices=['READ', 'MODIFY', 'FULL_ACCESS']),
        )),
        resourceGroups=dict(type='list'),
        users=dict(type='list'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('role', 'permissions'),
        ],
        required_one_of=[
            ('role', 'permissions'),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    state = module.params.get('state')
    role = module.params.get('role')
    resourceGroups = module.params.get('resourceGroups')
    permissions = module.params.get('permissions')
    users = module.params.get('users')

    # Role vs permissions
    if role:
        permissions = conn.retrive_list(f"userGroups/roles/{role}/permissions")
        permissions = [{'access': p['access'], 'resource': p['resource']} for p in permissions]
    else:
        role = 'CUSTOM'
        
    if state == 'present':
        accountSecurityProfileId = None
        pname = module.params.get('accountSecurityProfile')
        for p in conn.retrive_list('accountSecurity'):
            if p['name'] == pname:
                accountSecurityProfileId = p['id']
                break
        if not accountSecurityProfileId:
            module.fail_json(msg=f"AccountSecurityProfile '{pname}' not found")

    query = dict(
        fullTextSearch=dict(
            type="OR",
            value=name,
            fields=["name"]
        )
    )
    groups = conn.post('userGroups/query', payload=query, expected_code=200)
    
    current_group = None
    for group in groups['list']:
        if group['name'] == name:
            current_group = conn.get(f"userGroups/{group['id']}?includeUsers=True")
            result['group'] = group

    # Create
    if current_group is None and state == 'present':
        result['changed'] = True
        new_group = dict(
            name=name,
            role=role,
            resourceGroups=resourceGroups,
            permissions=permissions,
            accountSecurityProfileId=accountSecurityProfileId,
            users=users,
        )
        if not module.check_mode:
            resp = conn.post('userGroups', payload=new_group)
            new_group = conn.get(f"userGroups/{resp['id']}")

    # Update
    elif state == 'present':
        update = dict(id=current_group['id'])
        for key in ['role', 'accountSecurityProfileId']:
            value = module.params.get(key)
            if value and current_group[key] != value:
                update[key] = value

        # permissions
        perm_current = [{'access': r['access'], 'resource': r['resource']} for r in current_group['permissions']]
        if perm_current != permissions:
            update['permissions'] = permissions

        # resourceGroups
        rg_current = [{'id': r['id'], 'type': r['type']} for r in current_group['resourceGroups']]
        if rg_current != resourceGroups:
            update['resourceGroups'] = resourceGroups

        # users
        rusers_current = sorted(u['id'] for u in current_group['users'])
        if rusers_current != sorted(u['id'] for u in users):
            update['users'] = users

        if len(update) > 1:
            result['changed'] = True
            result['update'] = update
            if not module.check_mode:
                users = conn.patch(f"userGroups/{current_group['id']}", payload=update)
                new_group = conn.get(f"userGroups/{current_group['id']}")
            else:
                new_group = copy.deepcopy(current_group)
                new_group.update(update)

    # Delete
    elif current_group is not None and state == 'absent':
        result['changed'] = True
        new_group = None
        if not module.check_mode:
            conn.delete(f"users/{current_group['id']}")

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(before=current_group, after=new_group)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
