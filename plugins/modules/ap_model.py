#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap_model

short_description: Manage AP Model settings

description: Manage AP Model settings in a zone or group

options:
    zone:
        description: Zone to set modle config in
        type: str
        required: true
    group:
        description: AP group to set model config in
        type: str
    model:
        description: Model to set config for
        type: str
        required: true
    lan_port:
        description: Lan port config to set
        type: dict
        suboptions:
            lan1:
                description: Lan port 1 config
                type: dict
                suboptions:
                    enabled:
                        description: Enable or disbale port
                        type: bool
                        default: True
                    profile:
                        description: Name of profile to use
                        type: str
            lan2:
                description: Lan port 2 config
                type: dict
                suboptions:
                    enabled:
                        description: Enable or disbale port
                        type: bool
                        default: True
                    profile:
                        description: Name of profile to use
                        type: str
            lan3:
                description: Lan port 3 config
                type: dict
                suboptions:
                    enabled:
                        description: Enable or disbale port
                        type: bool
                        default: True
                    profile:
                        description: Name of profile to use
                        type: str
            lan4:
                description: Lan port 4 config
                type: dict
                suboptions:
                    enabled:
                        description: Enable or disbale port
                        type: bool
                        default: True
                    profile:
                        description: Name of profile to use
                        type: str
            lan5:
                description: Lan port 5 config
                type: dict
                suboptions:
                    enabled:
                        description: Enable or disbale port
                        type: bool
                        default: True
                    profile:
                        description: Name of profile to use
                        type: str

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure AP Model Configuration for R560
  ap_model:
    zone: Default
    model: R560
    lan_port:
      lan2:
        profile: NAC Trunk
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        group=dict(type='str'),
        model=dict(type='str', required=True),
        lan_port=dict(type='dict', default=None, options=dict(
            lan1=dict(type='dict', default=None, options=dict(
                enabled=dict(type='bool', default=True),
                profile=dict(type='str'),
            )),
            lan2=dict(type='dict', default=None, options=dict(
                enabled=dict(type='bool', default=True),
                profile=dict(type='str'),
            )),
            lan3=dict(type='dict', default=None, options=dict(
                enabled=dict(type='bool', default=True),
                profile=dict(type='str'),
            )),
            lan4=dict(type='dict', default=None, options=dict(
                enabled=dict(type='bool', default=True),
                profile=dict(type='str'),
            )),
            lan5=dict(type='dict', default=None, options=dict(
                enabled=dict(type='bool', default=True),
                profile=dict(type='str'),
            )),
        )),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    group = module.params.get('group')
    model = module.params.get('model')
    lan_port = module.params.get('lan_port') or {}

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone, required=True)
    ressource = f"rkszones/{zone['id']}/apmodel/{model}"
    if group:
        group = conn.retrive_by_name(f"rkszones/{zone['id']}/apgroups", group, required=True)
        ressource = f"rkszones/{zone['id']}/apgroups/{group['id']}/apmodel/{model}"

    # Get current group
    current_config = conn.get(ressource)
    result['config'] = current_config

    # Update Lan Ports
    new_config = copy.deepcopy(current_config)
    for port in new_config['lanPorts']:
        new_port = lan_port.get(port['portName'].lower())
        if not new_port:
            continue
        port['enabled'] = new_port['enabled']
        if new_port['profile']:
            profile = conn.retrive_by_name(f"rkszones/{zone['id']}/profile/ethernetPort", new_port['profile'], required=True)
            port['ethPortProfile'] = dict(
                id=profile['id'],
                name=profile['name'],
            )

    if new_config != current_config:
        result['changed'] = True
        if not module.check_mode:
            for key in [k for k in new_config if new_config[k] is None]:
                del new_config[key]
            conn.put(ressource, payload=new_config)
            new_config = conn.get(ressource)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_config,
            after=new_config,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
