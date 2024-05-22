#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ftp

short_description: Manage FTP servers

description: Manage FTP servers

options:
    name:
        description: FTP server name
        type: str
        required: True
    protocol:
        description: FTP protocol to use.
        type: str
        choices: [FTP, SFTP]
    host:
        description: Server hostname or ip
        type: str
    port:
        description: Server port. Defaults to 21 for FTP ans 22 for SFTP.
        type: int
    username:
        description: Username to autenticate to the server
        type: str
    password:
        description: Password to autenticate to the server
        type: str
    remote_directory:
        description: Remote directory path
        type: str
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup SFTP
  ftp:
    name: SFTP
    protocol: SFTP
    host: sftp.example.com
    username: smartzoneuser

- name: Setup FTP
  ftp:
    name: FTP
    protocol: FTP
    host: ftp.example.com
    username: smartzoneuser
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        protocol=dict(type='str', choices=['FTP', 'SFTP']),
        host=dict(type='str'),
        port=dict(type='int'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        remote_directory=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('protocol', 'host'), False),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    protocol = module.params.get('protocol')
    host = module.params.get('host')
    port = module.params.get('protocol') or 21 if protocol == 'FTP' else 22
    username = module.params.get('username')
    password = module.params.get('password')
    remote_directory = module.params.get('remote_directory')
    state = module.params.get('state')

    # Get current state
    current_ftp = None
    query = dict(
        fullTextSearch=dict(
            type="OR",
            value=name,
            fields=["ftpName"]
        )
    )
    ftps = conn.post('ftps/query', payload=query, expected_code=200)
    for server in ftps['list']:
        if server['ftpName'] == name:
            current_ftp = server

    # Create
    if current_ftp is None and state == 'present':
        result['changed'] = True
        new_ftp = dict(
            ftpName=name,
            ftpProtocol=protocol,
            ftpHost=host,
            ftpPort=port,
        )
        if username:
            new_ftp['ftpUserName'] = username
        if password:
            new_ftp['ftpPassword'] = password
        if remote_directory:
            new_ftp['ftpRemoteDirectory'] = remote_directory

        if not module.check_mode:
            conn.post('ftps', payload=new_ftp)
            ftps = conn.post('ftps/query', payload=query, expected_code=200)
            for server in ftps['list']:
                if server['ftpName'] == name:
                    new_ftp = server
        result['ftp'] = new_ftp
    # Update
    elif state == 'present':
        update_ftp = dict()
        for key, value in {
            'ftpProtocol': protocol,
            'ftpHost': host,
            'ftpPort': port,
            'ftpUserName': username,
            'ftpPassword': password,
            'ftpRemoteDirectory': remote_directory,

        }.items():
            if value and current_ftp.get(key) != value:
                update_ftp[key] = value

        result['ftp'] = current_ftp
        if update_ftp:
            result['changed'] = True
            if not module.check_mode:
                conn.patch(f"ftps/{current_ftp['id']}", payload=update_ftp)
                new_ftp = conn.get(f"ftps/{current_ftp['id']}")
            else:
                new_ftp = copy.deepcopy(current_ftp)
                new_ftp.update(update_ftp)
            result['ftp'] = new_ftp

    # Delete
    elif current_ftp is not None and state == 'absent':
        result['changed'] = True
        if not module.check_mode:
            conn.delete(f"ftps/{current_ftp['id']}")
        new_ftp = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_ftp,
            after=new_ftp,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
