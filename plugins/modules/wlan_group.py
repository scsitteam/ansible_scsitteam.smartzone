#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: wlan_group

short_description: Manage FTP servers

description: Manage FTP servers

options:
    zone:
        description: Zone to manage wlan group in
        type: str
        required: true
    name:
        description: Wlan group name
        type: str
        required: true
    description:
        description: Wlan group description
        type: str
    state:
        description: Desired state of the ap group
        type: str
        default: present
        choices: ['present', 'absent']


author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup WLAN Groups
  wlan_group:
    zone: Ansible
    name: 2G
    description: "2.4G WLAN Group"
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    name = module.params.get('name')
    description = module.params.get('description')
    state = module.params.get('state')

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone)

    # Get current group
    current_group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", name)

    # Create
    if current_group is None and state == 'present':
        new_group = dict(
            name=name
        )
        if description:
            new_group['description'] = description

        result['changed'] = True
        if not module.check_mode:
            conn.post(f"rkszones/{zone['id']}/wlangroups", json=new_group)
            new_group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", name)

    # Update
    elif state == 'present':
        update_group = dict()
        if current_group['description'] != description:
            update_group['description'] = description

        if update_group:
            result['changed'] = True
            if not module.check_mode:
                conn.patch(f"rkszones/{zone['id']}/wlangroups/{current_group['id']}", json=update_group)
                new_group = conn.get(f"rkszones/{zone['id']}/wlangroups/{current_group['id']}")
            else:
                new_group = copy.deepcopy(current_group)
                new_group.update(update_group)

    # Delete
    elif current_group is not None and state == 'absent':
        result['changed'] = True
        new_group = None
        if not module.check_mode:
            conn.delete(f"rkszones/{zone['id']}/wlangroups/{current_group['id']}")

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_group,
            after=new_group,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
