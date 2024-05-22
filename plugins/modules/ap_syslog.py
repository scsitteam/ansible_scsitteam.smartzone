#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap_syslog

short_description: Setup SmartZone AP Syslog Profile

description: Setup SmartZone AP Syslog Profile

options:
    name:
        description: Name of the Syslog Profile
        type: str
        required: true
    description:
        description: description of the Syslog Profile
        type: str
    primary_address:
        description: Address of the primary syslog server
        type: str
    primary_port:
        description: Port of the primary syslog server
        type: int
        default: 514
    primary_protocol:
        description: protocol for the primary syslog server. IPPROTO_UDP or IPPROTO_TCP.
        type: str
        default: IPPROTO_TCP
        choices: [IPPROTO_UDP, IPPROTO_TCP]
    secondary_address:
        description: Address of the secondary syslog server
        type: str
    secondary_port:
        description: Port of the secondary syslog server
        type: int
        default: 514
    secondary_protocol:
        description: protocol for the secondary syslog server. IPPROTO_UDP or IPPROTO_TCP.
        type: str
        default: IPPROTO_TCP
        choices: [IPPROTO_UDP, IPPROTO_TCP]
    redundancy_mode:
        description: Redundancy mode ACTIVE_ACTIVE or PRIMARY_BACKUP.
        type: str
        default: ACTIVE_ACTIVE
        choices: [ACTIVE_ACTIVE, PRIMARY_BACKUP]
    flow_level:
        description: Logs to send. GENERAL_LOGS, CLIENT_FLOW or ALL_LOGS.
        type: str
        default: GENERAL_LOGS
        choices: [GENERAL_LOGS, CLIENT_FLOW, ALL_LOGS]
    state:
        description: State of the syslog profile.
        type: str
        default: present
        choices: [present, absent]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup SNMP for APs
  ap_snmp:
    name: public
    snmpv2:
      - community: public
        read: true
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        primary_address=dict(type='str'),
        primary_port=dict(type='int', default=514),
        primary_protocol=dict(type='str', default='IPPROTO_TCP', choices=['IPPROTO_UDP', 'IPPROTO_TCP']),
        secondary_address=dict(type='str'),
        secondary_port=dict(type='int', default=514),
        secondary_protocol=dict(type='str', default='IPPROTO_TCP', choices=['IPPROTO_UDP', 'IPPROTO_TCP']),
        redundancy_mode=dict(type='str', default='ACTIVE_ACTIVE', choices=['ACTIVE_ACTIVE', 'PRIMARY_BACKUP']),
        flow_level=dict(type='str', default='GENERAL_LOGS', choices=['GENERAL_LOGS', 'CLIENT_FLOW', 'ALL_LOGS']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    domain = module.params.get('domain')
    name = module.params.get('name')
    description = module.params.get('description')
    primary_address = module.params.get('primary_address')
    primary_port = module.params.get('primary_port')
    primary_protocol = module.params.get('primary_protocol')
    secondary_address = module.params.get('secondary_address')
    secondary_port = module.params.get('secondary_port')
    secondary_protocol = module.params.get('secondary_protocol')
    redundancy_mode = module.params.get('redundancy_mode')
    flow_level = module.params.get('flow_level')
    state = module.params.get('state')

    # Get current syslog
    current_syslog = conn.retrive_by_name(f"apSyslogServerProfiles?domainId={conn.domainId}", name)

    # Create
    if current_syslog is None and state == 'present':
        new_syslog = dict(
            domainId=conn.domainId,
            name=name,
            primaryAddress=primary_address,
            primaryPort=primary_port,
            primaryProtocol=primary_protocol,
            redundancyMode=redundancy_mode,
            flowLevel=flow_level,
        )
        if description:
            new_syslog['description'] = description
        if secondary_address:
            new_syslog['secondaryAddress'] = secondary_address
            new_syslog['secondaryPort'] = secondary_port
            new_syslog['secondaryProtocol'] = secondary_protocol

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('apSyslogServerProfiles', payload=new_syslog)
            new_syslog = conn.get(f"apSyslogServerProfiles/{resp['id']}")

    # Update
    elif state == 'present':
        update_syslog = copy.deepcopy(current_syslog)
        if description:
            update_syslog['description'] = description
        update_syslog['primaryAddress'] = primary_address
        if primary_port:
            update_syslog['primaryPort'] = primary_port
        if primary_protocol:
            update_syslog['primaryProtocol'] = primary_protocol
        if secondary_address:
            update_syslog['secondaryAddress'] = secondary_address
            update_syslog['secondaryPort'] = secondary_port
            update_syslog['secondaryProtocol'] = secondary_protocol
        if redundancy_mode:
            update_syslog['redundancyMode'] = redundancy_mode
        if flow_level:
            update_syslog['flowLevel'] = flow_level

        if update_syslog != current_syslog:
            result['changed'] = True
            if not module.check_mode:
                for key in ['createDateTime', 'creatorUsername', 'domainId', 'id', 'modifiedDateTime', 'modifierUsername']:
                    del update_syslog[key]
                conn.put(f"apSyslogServerProfiles/{current_syslog['id']}", payload=update_syslog)
                new_syslog = conn.get(f"apSyslogServerProfiles/{current_syslog['id']}")
            else:
                new_syslog = copy.deepcopy(current_syslog)
                new_syslog.update(update_syslog)

    # Delete
    elif current_syslog is not None and state == 'absent':
        result['changed'] = True
        if not module.check_mode:
            resp = conn.delete(f"apSyslogServerProfiles/{current_syslog['id']}", expected_code=200)
        new_syslog = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_syslog,
            after=new_syslog,
        )
    module.exit_json(**result, current_syslog=current_syslog)


if __name__ == '__main__':
    main()
