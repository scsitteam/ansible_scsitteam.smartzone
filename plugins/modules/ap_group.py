#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap_group

short_description: Manage ap group

description: Manage ap group

options:
    zone:
        description: Zone zo mange groups in
        type: str
        required: true
    name:
        description: AP group name
        type: str
        required: true
    radio_config:
        description: Ap group radio config
        type: dict
        suboptions:
            radio24g:
                description: Config for 2.4G radios
                type: dict
                suboptions:
                    wlan_group:
                        description: WLan group
                        type: str
            radio5g:
                description: Config for 5G radios
                type: dict
                suboptions:
                    wlan_group:
                        description: WLan group
                        type: str
            radio5gLower:
                description: Config for lower 5G radios
                type: dict
                suboptions:
                    wlan_group:
                        description: WLan group
                        type: str
            radio5gUpper:
                description: Config for upper 5G radios
                type: dict
                suboptions:
                    wlan_group:
                        description: WLan group
                        type: str
            radio6g:
                description: Config for 6G radios
                type: dict
                suboptions:
                    wlan_group:
                        description: WLan group
                        type: str
    state:
        description: Desired state of the ap group
        type: str
        default: present
        choices: ['present', 'absent']

extends_documentation_fragment:
- scsitteam.smartzone.ap_basic_config.documentation

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup Ap Group
  ap_group:
    zone: Ansible
    name: Group1
    location_additional: Rack 1
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection
from ansible_collections.scsitteam.smartzone.plugins.module_utils.params import ApBasicConfig


def main():
    argument_spec_radio = dict(type='dict', default=None, options=dict(
        wlan_group=dict(type='str'),
    ))

    argument_spec = ApBasicConfig.argument_spec()
    argument_spec.update(dict(
        zone=dict(type='str', required=True),
        name=dict(type='str', required=True),
        radio_config=dict(type='dict', default=None, options=dict(
            radio24g=argument_spec_radio,
            radio5g=argument_spec_radio,
            radio5gLower=argument_spec_radio,
            radio5gUpper=argument_spec_radio,
            radio6g=argument_spec_radio,
        )),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=ApBasicConfig.required_together()
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    name = module.params.get('name')
    radio_config = module.params.get('radio_config')
    ap_basic_config = ApBasicConfig(module.params)
    state = module.params.get('state')

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone)

    # Get current group
    current_group = conn.retrive_by_name(f"rkszones/{zone['id']}/apgroups", name)
    result['current_group'] = current_group

    # Create
    if current_group is None and state == 'present':
        new_group = dict(
            name=name
        )
        ap_basic_config.update(new_group)

        for rtype in radio_config:
            if not radio_config[rtype]:
                continue
            if radio_config[rtype]['wlan_group']:
                group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", radio_config[rtype]['wlan_group'], required=True)
                if 'radioConfig' not in new_group:
                    new_group['radioConfig'] = {}
                if rtype not in new_group['radioConfig']:
                    new_group['radioConfig'][rtype] = {}
                new_group['radioConfig'][rtype]['wlanGroupId'] = group['id']

        result['changed'] = True
        if not module.check_mode:
            conn.post(f"rkszones/{zone['id']}/apgroups", payload=new_group)
            new_group = conn.retrive_by_name(f"rkszones/{zone['id']}/apgroups", name)

    # Update
    elif state == 'present':
        update_group = dict()
        ap_basic_config.update(update_group, current_group)

        for rtype in radio_config:
            if not radio_config[rtype]:
                continue
            if rtype not in current_group['radioConfig']:
                continue
            if radio_config[rtype]['wlan_group']:
                group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", radio_config[rtype]['wlan_group'], required=True)
                if current_group['radioConfig'][rtype]['wlanGroupId'] != group['id']:
                    if 'radioConfig' not in update_group:
                        update_group['radioConfig'] = {}
                    if rtype not in update_group['radioConfig']:
                        update_group['radioConfig'][rtype] = {}
                    update_group['radioConfig'][rtype]['wlanGroupId'] = group['id']

        if update_group:
            result['changed'] = True
            if not module.check_mode:
                for key in [k for k in update_group if update_group[k] is None]:
                    conn.delete(f"rkszones/{zone['id']}/apgroups/{current_group['id']}/{key}")
                    del update_group[key]
                conn.patch(f"rkszones/{zone['id']}/apgroups/{current_group['id']}", payload=update_group)
                new_group = conn.get(f"rkszones/{zone['id']}/apgroups/{current_group['id']}")
            else:
                new_group = copy.deepcopy(current_group)
                new_group.update(update_group)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_group,
            after=new_group,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
