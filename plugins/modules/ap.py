#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap

short_description: Manage FTP servers

description: Manage FTP servers

options:
    mac:
        description: MAC of the ap
        type: str
        required: True
    name:
        description: Name of the ap
        type: str
    zone:
        description: Zone of the ap
        type: str
    group:
        description: Group of the ap
        type: str
    state:
        description: State of the ap
        type: str
        default: keep
        choices: [keep, present, absent]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup Access Points
  ap:
    mac: 00:11:22:33:44:55
    name: ap01
    zone: Ansible
    group: Ansible
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        mac=dict(type='str', required=True),
        name=dict(type='str'),
        zone=dict(type='str'),
        group=dict(type='str'),
        state=dict(type='str', default='keep', choices=['present', 'absent', 'keep']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    mac = module.params.get('mac')
    name = module.params.get('name')
    zone = module.params.get('zone')
    group = module.params.get('group')
    state = module.params.get('state')

    # Get current group
    code, current_ap = conn._cli.send_request(None, f"aps/{mac}", method='GET')
    if code == 403 and state == 'keep':
        module.exit_json(skipped=True, msg=f"Access Point {mac} not found.", **result)

    # Resolve Zone and Group
    if zone:
        zone = conn.retrive_by_name('rkszones', zone)
    if group:
        group = conn.retrive_by_name(f"rkszones/{zone['id']}/apgroups", group)

    # Update
    update_ap = dict()
    if current_ap['name'] != name:
        update_ap['name'] = name
    if zone and current_ap['zoneId'] != zone['id']:
        update_ap['zoneId'] = zone['id']
    if group and current_ap['apGroupId'] != group['id']:
        update_ap['apGroupId'] = group['id']

    if update_ap:
        result['changed'] = True
        if not module.check_mode:
            resp = conn.patch(f"aps/{mac}", payload=update_ap)
            new_ap = conn.get(f"aps/{mac}")
        else:
            new_ap = copy.deepcopy(current_ap)
            new_ap.update(update_ap)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_ap,
            after=new_ap,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
