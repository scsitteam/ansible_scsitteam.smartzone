#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: aaa_radius

short_description: Manage AAA Radius Server

description: Manage AAA Radius Server

options:
    zone:
        description: Zone to configure aaa radius server in.
        type: str
        required: True
    name:
        description: Name of the aaa radius server.
        type: str
        required: True
    description:
        description: Description of the aaa radius server.
        type: str
    primary:
        description: Primary radius server.
        type: dict
        suboptions:
            ip:
                description: Radius server ip.
                type: str
                required: True
            port:
                description: Radius server port.
                type: int
                default: 1812
            sharedSecret:
                description: Radius server shared secret
                type: str
                required: True
            sharedSecret_update:
                description: Should the Radius server shared secret be updated.
                type: bool
                default: True
    secondary:
        description: Secondary radius server.
        type: dict
        suboptions:
            ip:
                description: Radius server ip.
                type: str
                required: True
            port:
                description: Radius server port.
                type: int
                default: 1812
            sharedSecret:
                description: Radius server shared secret
                type: str
                required: True
            sharedSecret_update:
                description: Should the Radius server shared secret be updated.
                type: bool
                default: True
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure Radius
  aaa_radius:
    zone: Default
    name: RadiusServer
    primary:
      ip: 192.168.0.10
      sharedSecret: secret
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        primary=dict(type='dict', default=None, options=dict(
            ip=dict(type='str', required=True),
            port=dict(type='int', default=1812),
            sharedSecret=dict(type='str', required=True, no_log=True),
            sharedSecret_update=dict(type='bool', default=True, no_log=False),
        )),
        secondary=dict(type='dict', default=None, options=dict(
            ip=dict(type='str', required=True),
            port=dict(type='int', default=1812),
            sharedSecret=dict(type='str', required=True, no_log=True),
            sharedSecret_update=dict(type='bool', default=True, no_log=False),
        )),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('primary',)),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    name = module.params.get('name')
    description = module.params.get('description')
    primary = module.params.get('primary')
    secondary = module.params.get('secondary')
    state = module.params.get('state')

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone, required=True)

    # Get current zone
    current_aaa = conn.retrive_by_name(f"rkszones/{zone['id']}/aaa/radius", name)
    if 'sharedSecret' in current_aaa['primary']:
        module.no_log_values.update([current_aaa['primary']['sharedSecret']])
    if 'sharedSecret' in current_aaa['secondary']:
        module.no_log_values.update([current_aaa['secondary']['sharedSecret']])

    # Create
    if current_aaa is None and state == 'present':
        new_aaa = dict(
            name=name,
            primary={key: primary[key] for key in primary if not key.endswith('_update')},
        )
        if description:
            new_aaa['description'] = description
        if secondary:
            new_aaa['secondary'] = {key: secondary[key] for key in secondary if not key.endswith('_update')}

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post(f"rkszones/{zone['id']}/aaa/radius", payload=new_aaa)
            new_zone = conn.get(f"rkszones/{resp['id']}/aaa/radius/{resp['id']}")

    # Update
    elif state == 'present':
        update_aaa = dict()

        if primary and any(
            current_aaa['primary'].get(key) != primary[key]
            for key in primary
            if not key.endswith('_update') and primary.get(f"{key}_update", True)
        ):
            update_aaa['primary'] = {
                key: primary[key]
                for key in primary
                if not key.endswith('_update') and (primary.get(f"{key}_update", True) or current_aaa['primary'] is None)
            }

        if description and current_aaa['description'] != description:
            update_aaa['description'] = description

        if secondary and (current_aaa['secondary'] is None or any(
            current_aaa['secondary'].get(key) != secondary[key]
            for key in secondary
            if not key.endswith('_update') and secondary.get(f"{key}_update", True)
        )):
            update_aaa['secondary'] = {
                key: value
                for key, value in secondary.items()
                if not key.endswith('_update') and (secondary.get(f"{key}_update", True) or current_aaa['secondary'] is None)
            }

        if update_aaa:
            result['changed'] = True
            if not module.check_mode:
                resp = conn.patch(f"rkszones/{zone['id']}/aaa/radius/{current_aaa['id']}", payload=update_aaa)
                new_aaa = conn.get(f"rkszones/{zone['id']}/aaa/radius/{current_aaa['id']}")
            else:
                new_aaa = copy.deepcopy(current_aaa)
                new_aaa.update(update_aaa)

        # Delete
        if current_aaa is not None and state == 'absent':
            result['changed'] = True
            if not module.check_mode:
                conn.delete(f"rkszones/{resp['id']}/aaa/radius/{resp['id']}")
            new_aaa = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_aaa,
            after=new_aaa,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
