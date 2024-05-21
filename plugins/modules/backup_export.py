#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: backup_export

short_description: Configures the backup auto export

description: Configures the backup auto export

options:
    state:
        description: Set the state of the export
        type: str
        default: enabled
        choices: [enabled, disabled]
    server:
        description: Name of the (S)FTP server to use
        type: str
    prefix:
        description: Prefix for the file name
        type: str

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup SmartZone Backup FTP Export
  backup_export:
    server: BackupServer
    prefix: "{{ inventory_hostname }}"
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        state=dict(type='str', default='enabled', choices=['enabled', 'disabled']),
        server=dict(type='str'),
        prefix=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'enabled', ('server', 'prefix'), False),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    state = module.params.get('state')
    server = module.params.get('server')
    prefix = module.params.get('prefix')

    # Get current config
    current_export = conn.get('configurationSettings/autoExportBackup')

    # Update
    update_export = dict()
    if current_export['enableAutoExportBackup'] != (state == 'enabled'):
        update_export['enableAutoExportBackup'] = (state == 'enabled')
    if server and current_export['ftpServer'] != server:
        update_export['ftpServer'] = server
    if prefix and current_export['ftpNamePrefix'] != prefix:
        update_export['ftpNamePrefix'] = prefix

    if update_export:
        result['changed'] = True
        if not module.check_mode:
            conn.patch('configurationSettings/autoExportBackup', payload=update_export)
            new_export = conn.get('configurationSettings/autoExportBackup')
        else:
            new_export = copy.deepcopy(current_export)
            new_export.update(update_export)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_export,
            after=new_export,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
