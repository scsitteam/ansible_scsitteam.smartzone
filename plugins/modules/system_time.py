#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: system_time

short_description: Manage SmartZone system time config

description: Manage system time zone and ntp servers.

options:
    timezone:
        description: Timezone to use.
        type: str
    ntp_server:
        description: IP/DNS of primary ntp server.
        type: str
    secondary_ntp_server:
        description: IP/DNS of secondary ntp server.
        type: str
    third_ntp_server:
        description: IP/DNS of third ntp server.
        type: str

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
---
- name: Set Timezone
  system_time:
    timezone: Europe/Zurich

- name: Set NTP Server
  system_time:
    ntp_server: 192.168.0.10
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        timezone=dict(type='str'),
        ntp_server=dict(type='str'),
        secondary_ntp_server=dict(type='str'),
        third_ntp_server=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    timezone = module.params.get('timezone')
    ntp_server = module.params.get('ntp_server')
    secondary_ntp_server = module.params.get('secondary_ntp_server')
    third_ntp_server = module.params.get('third_ntp_server')

    current_time = conn.get('system/systemTime')
    result['system_time'] = {k: v for k, v in current_time.items() if not k.endswith('Key')}
    update_time = dict()

    if current_time['timezone'] != timezone:
        update_time['timezone'] = timezone

    if ntp_server is not None and current_time['ntpServer'] != ntp_server:
        update_time['ntpServer'] = ntp_server

    if secondary_ntp_server is not None and current_time['secondaryNtpServer'] != secondary_ntp_server:
        update_time['secondaryNtpServer'] = secondary_ntp_server

    if third_ntp_server is not None and current_time['thirdNtpServer'] != third_ntp_server:
        update_time['thirdNtpServer'] = third_ntp_server

    if update_time:
        result['changed'] = True
        if not module.check_mode:
            conn.patch('system/systemTime', payload=update_time)
            new_time = conn.get('system/systemTime')
        else:
            new_time = copy.deepcopy(current_time)
            new_time.update(update_time)
        result['system_time'] = {k: v for k, v in new_time.items() if not k.endswith('Key')}

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before={k: v for k, v in current_time.items() if not k.startswith('currentSystemTime')},
            after={k: v for k, v in new_time.items() if not k.startswith('currentSystemTime')},
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
