#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: dpsk

short_description: Manage FTP servers

description: Manage FTP servers

options:
    zone:
        description: Zone to manage D-PSK in
        type: str
        required: True
    wlan:
        description: wlan to manage D-PSK for
        type: str
        required: True
    username:
        description: User name of the D-PSK
        type: str
        required: True
    vlan:
        description: VLan ID for the D-PSK
        type: int
    group_dpsk:
        description: Is this group D-PSK
        type: bool
        default: false
    state:
        description: Desired state of the D-PSK
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure D-PSG
  dpsk:
    zone: Ansible
    wlan: DPSK-Labor
    username: Ansible
    vlan: 42
    group_dpsk: True
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

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        wlan=dict(type='str', required=True),
        username=dict(type='str', required=True),
        vlan=dict(type='int'),
        group_dpsk=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    wlan = module.params.get('wlan')
    username = module.params.get('username')
    vlan = module.params.get('vlan')
    group_dpsk = module.params.get('group_dpsk')
    state = module.params.get('state')
    zone = conn.retrive_by_name('rkszones', zone, required=True)
    wlan = conn.retrive_by_name(f"rkszones/{zone['id']}/wlans", wlan, required=True)

    # Get current dpks
    current_dpsk = None
    for dpsk in conn.retrive_list(f"rkszones/{zone['id']}/wlans/{wlan['id']}/dpsk"):
        if dpsk['userName'] == username:
            current_dpsk = dpsk
            module.no_log_values.update([current_dpsk['passphrase']])
            break

    # Create
    if current_dpsk is None and state == 'present':
        result['changed'] = True
        new_dpsk = dict(
            amount=1,
            userName=username,
            groupDpsk=group_dpsk
        )
        if vlan:
            new_dpsk['vlanId'] = vlan

        if not module.check_mode:
            conn.post(f"rkszones/{zone['id']}/wlans/{wlan['id']}/dpsk/batchGenUnbound", payload=new_dpsk)
            new_dpsk = None
            for dpsk in conn.retrive_list(f"rkszones/{zone['id']}/wlans/{wlan['id']}/dpsk"):
                if dpsk['userName'] == username:
                    new_dpsk = dpsk
                    module.no_log_values.update([new_dpsk['passphrase']])
                    break
    elif current_dpsk is not None and state == 'absent':
        result['changed'] = True
        new_dpsk = None

        if not module.check_mode:
            payload = dict(idList=[current_dpsk['id']])
            conn.post(f"rkszones/{zone['id']}/wlans/{wlan['id']}/dpsk", payload=payload, expected_code=200)
            for dpsk in conn.retrive_list(f"rkszones/{zone['id']}/wlans/{wlan['id']}/dpsk"):
                if dpsk['userName'] == username:
                    new_dpsk = dpsk
                    module.no_log_values.update([new_dpsk['passphrase']])
                    break

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_dpsk,
            after=new_dpsk,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
