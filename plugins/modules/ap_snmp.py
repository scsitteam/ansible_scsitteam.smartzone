#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap_snmp

short_description: Setup SmartZone AP SNMP Profile

description: Setup SmartZone AP SNMP Profile

options:
    name:
        description: Name of the SNMP Profile
        type: str
        required: true
    description:
        description: description of the SNMP Profile
        type: str
    snmpv2:
        description: SNMP v2 configuration
        type: list
        elements: dict
        suboptions:
            communityName:
                description: SNMP v2 community string
                type: str
                required: true
                aliases: [community]
            readEnabled:
                description: Enable read access
                type: bool
                default: False
                aliases: [read]
            writeEnabled:
                description: Write read access
                type: bool
                default: False
                aliases: [write]
            notificationEnabled:
                description: Enables SNPNM v2 notifications
                type: bool
                default: False
                aliases: [notify]
            notificationType:
                description: Notification type
                type: str
                choices: [TRAP, INFORM]
            notificationTarget:
                description: Target for the SNPNM v2 notifications
                type: list
                elements: dict
                suboptions:
                    address:
                        description: Notification target IP address.
                        type: str
                        required: True
                    port:
                        description: Notification target port.
                        type: int
                        required: True
    snmpv3:
        description: SNMP V3 configuration
        type: list
        elements: dict
        suboptions:
            userName:
                description: SNMP v3 username
                type: str
                required: true
                aliases: [user]
            authProtocol:
                description: SNMP v3 authentication protocoll
                type: str
                choices: [MD5, SHA]
                aliases: [auth_protocol]
            authPassword:
                description: SNMP v3 authentication password
                type: str
                aliases: [auth_password]
            privProtocol:
                description: SNMP v3 privacy protocoll
                type: str
                choices: [DES, AES]
                aliases: [priv_protocol]
            privPassword:
                description: SNMP v3 privacy password
                type: str
                aliases: [priv_password]
            readEnabled:
                description: Enable read access
                type: bool
                default: False
                aliases: [read]
            writeEnabled:
                description: Write read access
                type: bool
                default: False
                aliases: [write]
            notificationEnabled:
                description: Enables SNPNM v2 notifications
                type: bool
                default: False
                aliases: [notify]
            notificationType:
                description: Notification type
                type: str
                choices: [TRAP, INFORM]
            notificationTarget:
                description: Target for the SNPNM v2 notifications
                type: list
                elements: dict
                suboptions:
                    address:
                        description: Notification target IP address.
                        type: str
                        required: True
                    port:
                        description: Notification target port.
                        type: int
                        required: True
    state:
        description: State of the syslog profile.
        type: str
        default: present
        choices: [present, absent]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup Syslog Server for APs
  ap_syslog:
    name: APSYSLOG
    primary_address: 192.168.0.10
    flow_level: ALL_LOGS
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        snmpv2=dict(
            type='list',
            elements='dict',
            options=dict(
                communityName=dict(type='str', required=True, aliases=['community']),
                readEnabled=dict(type='bool', default=False, aliases=['read']),
                writeEnabled=dict(type='bool', default=False, aliases=['write']),
                notificationEnabled=dict(type='bool', default=False, aliases=['notify']),
                notificationType=dict(type='str', choices=['TRAP', 'INFORM']),
                notificationTarget=dict(type='list', elements='dict', options=dict(
                    address=dict(type='str', required=True),
                    port=dict(type='int', required=True),
                )),
            ),
        ),
        snmpv3=dict(
            type='list',
            elements='dict',
            options=dict(
                userName=dict(type='str', required=True, aliases=['user']),
                authProtocol=dict(type='str', choices=['MD5', 'SHA'], aliases=['auth_protocol']),
                authPassword=dict(type='str', aliases=['auth_password'], no_log=True),
                privProtocol=dict(type='str', choices=['DES', 'AES'], aliases=['priv_protocol']),
                privPassword=dict(type='str', aliases=['priv_password'], no_log=True),
                readEnabled=dict(type='bool', default=False, aliases=['read']),
                writeEnabled=dict(type='bool', default=False, aliases=['write']),
                notificationEnabled=dict(type='bool', default=False, aliases=['notify']),
                notificationType=dict(type='str', choices=['TRAP', 'INFORM']),
                notificationTarget=dict(type='list', elements='dict', options=dict(
                    address=dict(type='str', required=True),
                    port=dict(type='int', required=True),
                )),
            ),
            required_together=[
                ('authProtocol', 'authPassword'),
                ('privProtocol', 'privPassword'),
            ]
        ),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    description = module.params.get('description')
    snmpv2 = module.params.get('snmpv2')
    if snmpv2:
        snmpv2 = [
            {
                k: v for k, v in agent.items() if k in argument_spec['snmpv2']['options'].keys() and v is not None
            } for agent in snmpv2
        ]
    snmpv3 = module.params.get('snmpv3')
    if snmpv3:
        snmpv3 = [
            {
                k: v for k, v in agent.items() if k in argument_spec['snmpv3']['options'].keys()
            } for agent in snmpv3
        ]
    state = module.params.get('state')

    # Get current syslog
    current_snmp = conn.retrive_by_name(f"apSnmpAgentProfiles?domainId={conn.domainId}", name)

    # Create
    if current_snmp is None and state == 'present':
        new_snmp = dict(
            domainId=conn.domainId,
            name=name,
        )
        if description:
            new_snmp['description'] = description
        if snmpv2:
            new_snmp['snmpV2Agent'] = snmpv2
        if snmpv3:
            new_snmp['snmpV3Agent'] = snmpv3

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('apSnmpAgentProfiles', payload=new_snmp)
            new_snmp = conn.get(f"apSnmpAgentProfiles/{resp['id']}")

    # Update
    elif state == 'present':
        update_snmp = copy.deepcopy(current_snmp)
        if description:
            update_snmp['description'] = description
        if snmpv2 and current_snmp['snmpV2Agent'] != snmpv2:
            update_snmp['snmpV2Agent'] = snmpv2
        if snmpv3 and current_snmp['snmpV3Agent'] != snmpv3:
            update_snmp['snmpV3Agent'] = snmpv3

        if update_snmp != current_snmp:
            result['changed'] = True
            if not module.check_mode:
                for key in ['domainId', 'id']:
                    del update_snmp[key]
                for key in [k for k in update_snmp if update_snmp[k] is None]:
                    del update_snmp[key]
                conn.put(f"apSnmpAgentProfiles/{current_snmp['id']}", payload=update_snmp)
                new_snmp = conn.get(f"apSnmpAgentProfiles/{current_snmp['id']}")
            else:
                new_snmp = copy.deepcopy(current_snmp)
                new_snmp.update(update_snmp)

    # Delete
    elif current_snmp is not None and state == 'absent':
        result['changed'] = True
        if not module.check_mode:
            conn.delete(f"apSnmpAgentProfiles/{current_snmp['id']}")
        new_snmp = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_snmp,
            after=new_snmp,
        )
    module.exit_json(**result)


if __name__ == '__main__':
    main()
