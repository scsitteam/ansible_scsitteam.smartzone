#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: system_syslog

short_description: Manage SmartZone syslog config

description: Manage Syslog Server connection without Priority.

options:
    state:
        description: Enable or disablde the syslog forwarding.
        type: str
        default: enabled
        choices: [enabled, disabled]
    primary_server:
        description: Primary syslog target server
        type: dict
        suboptions:
            host:
                description: IP/DNS of primary syslog server
                type: str
                required: true
            port:
                description: Communication Port to NTP Server
                type: int
                default: 514
            protocol:
                description: Protocoll (TCP/UDP)
                type: str
                default: UDP
                choices: [TCP, UDP]
    secondary_server:
        description: Secondary syslog target server
        type: dict
        suboptions:
            host:
                description: IP/DNS of primary syslog server
                type: str
                required: true
            port:
                description: Communication Port to NTP Server
                type: int
                default: 514
            protocol:
                description: Protocoll (TCP/UDP)
                type: str
                default: UDP
                choices: [TCP, UDP]
            redundancyMode:
                description: Secondary syslog redundancy mode.
                type: str
                default: active_active
                choices: [active_active, primary_backup]

author:
    - Adrian Kaier (@a3an-k)
'''

EXAMPLES = r'''
- name: Setup Syslog Server
  system_syslog:
    primary_server:
      host: 192.168.0.10
  tags: syslog
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        state=dict(type='str', default='enabled', choices=['enabled', 'disabled']),
        primary_server=dict(type='dict', default=None, options=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', default=514),
            protocol=dict(type='str', default='UDP', choices=['UDP', 'TCP']),
        )),
        secondary_server=dict(type='dict', default=None, options=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', default=514),
            protocol=dict(type='str', default='UDP', choices=['UDP', 'TCP']),
            redundancyMode=dict(type='str', default='active_active', choices=['active_active', 'primary_backup'])
        )),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    enabled = (module.params.get('state') == 'enabled')
    primary_syslog_server = module.params.get('primary_server')
    secondary_syslog_server = module.params.get('secondary_server')

    # Get current config
    current_syslog = conn.get('system/syslog')

    # Update
    update_syslog = dict()
    if current_syslog['enabled'] != enabled:
        update_syslog['enabled'] = enabled
    if primary_syslog_server and current_syslog['primaryServer'] != primary_syslog_server:
        update_syslog['primaryServer'] = primary_syslog_server
    if secondary_syslog_server and current_syslog['secondaryServer'] != secondary_syslog_server:
        update_syslog['secondaryServer'] = secondary_syslog_server

    if update_syslog:
        result['changed'] = True
        if not module.check_mode:
            conn.patch('system/syslog', payload=update_syslog)
            new_syslog = conn.get('system/syslog')
        else:
            new_syslog = copy.deepcopy(current_syslog)
            new_syslog.update(update_syslog)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_syslog,
            after=new_syslog,
        )
    module.exit_json(**result, current_syslog=current_syslog)


if __name__ == '__main__':
    main()
