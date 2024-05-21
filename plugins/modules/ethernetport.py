#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ethernetport

short_description: Manage DHCP pools

description: Manage DHCP pools

options:
    zone:
        description: Name of the zone to manage Pools in.
        type: str
        required: true
    name:
        description: Name of the pool.
        type: str
        required: true
    description:
        description: Description  of the pool.
        type: str
    type:
        description: Ethernet port type
        type: str
        choices: [AccessPort, TrunkPort, GeneralPort]
    access_type:
        description: Ethernet port access type
        type: str
        default: WAN
        choices: [WAN, TUNNEL, LAN]
    nac:
        description: 802.1x / NAC configuration
        type: dict
        suboptions:
            type:
                description: 802.1x configuration type
                type: str
                default: Disable
                choices: [Disable, Supplicant, PortBasedAuthenticator]
            authenticator:
                description: Authenticator configuration
                type: dict
                suboptions:
                    authentication:
                        description: Authentication configuration
                        type: dict
                        suboptions:
                            enableUseSCGasProxy:
                                description: Proxy authentication through smart zone
                                type: bool
                                default: False
                            server:
                                description: Authentication server to use
                                type: dict
                                suboptions:
                                    id:
                                        description: AAA server id
                                        type: str
                                    name:
                                        description: AAA server name
                                        type: str
                    disabledAccounting:
                        description: Disabled accounting
                        type: bool
                        default: False
                    accounting:
                        description: Accounting server to use
                        type: dict
                        suboptions:
                            enableUseSCGasProxy:
                                description: Proxy authentication through smart zone
                                type: bool
                                default: False
                            server:
                                description: Authentication server to use
                                type: dict
                                suboptions:
                                    id:
                                        description: AAA server id
                                        type: str
                                    name:
                                        description: AAA server name
                                        type: str
                    macAuthByPassEnabled:
                        description: MAC auth bypass
                        type: bool
                        default: False
            supplicant:
                description: Supplicant configuration
                type: dict
                suboptions:
                    type:
                        description: Supplicant type
                        type: str
                        required: True
                        choices: [MACAddress, Custom]
                    userName:
                        description: Supplicant username
                        type: str
                    password:
                        description: Supplicant password
                        type: str
                    password_update:
                        description: Should the supplicant password be updated
                        type: bool
                        default: True
    state:
        description: Desired state of the pool
        type: str
        default: present
        choices: [present, absent]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure Ethernet Port Profile
  ethernetport:
    zone: Default
    name: NAC Trunk
    description: Authenticate as smartzone
    type: TrunkPort
    nac:
      type: Supplicant
      supplicant:
        type: Custom
        userName: smartzone
        password: DEFAULTPASSWORD
        password_update: false
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        type=dict(type='str', choices=['AccessPort', 'TrunkPort', 'GeneralPort']),
        access_type=dict(type='str', default='WAN', choices=['WAN', 'TUNNEL', 'LAN']),
        nac=dict(
            type='dict',
            options=dict(
                type=dict(type='str', default='Disable', choices=['Disable', 'Supplicant', 'PortBasedAuthenticator']),
                authenticator=dict(type='dict', options=dict(
                    authentication=dict(type='dict', options=dict(
                        enableUseSCGasProxy=dict(type='bool', default=False),
                        server=dict(type='dict', options=dict(
                            id=dict(type='str'),
                            name=dict(type='str'),
                        )),
                    )),
                    disabledAccounting=dict(type='bool', default=False),
                    accounting=dict(type='dict', options=dict(
                        enableUseSCGasProxy=dict(type='bool', default=False),
                        server=dict(type='dict', options=dict(
                            id=dict(type='str'),
                            name=dict(type='str'),
                        )),
                    )),
                    macAuthByPassEnabled=dict(type='bool', default=False),
                )),
                supplicant=dict(type='dict', default=None, options=dict(
                    type=dict(type='str', required=True, choices=['MACAddress', 'Custom']),
                    userName=dict(type='str'),
                    password=dict(type='str', no_log=True),
                    password_update=dict(type='bool', default=True, no_log=False),
                )),
            ),
            mutually_exclusive=[
                ('authenticator', 'supplicant'),
            ],
            required_if=[
                ('type', 'Supplicant', ('supplicant',), False),
                ('type', 'PortBasedAuthenticator', ('authenticator',), False),
            ],
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
    zone = module.params.get('zone')
    name = module.params.get('name')
    description = module.params.get('description')
    type = module.params.get('type')
    access_type = module.params.get('access_type')
    nac = module.params.get('nac')
    state = module.params.get('state')

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone)

    # Get current syslog
    current_eth = conn.retrive_by_name(f"rkszones/{zone['id']}/profile/ethernetPort", name)
    result['eth'] = current_eth

    # Create
    if current_eth is None and state == 'present':
        # Check if password should be updated
        if nac and 'supplicant' in nac and 'password_update' in nac['supplicant']:
            del nac['supplicant']['password_update']

        new_eth = dict(
            name=name,
            type=type,
            accessNetworkType=access_type,
            _8021X=nac,
        )
        if description:
            new_eth['description'] = description

        result['changed'] = True
        result['eth'] = new_eth
        if not module.check_mode:
            resp = conn.post(f"rkszones/{zone['id']}/profile/ethernetPort", payload=new_eth)
            new_eth = conn.get(f"rkszones/{zone['id']}/profile/ethernetPort/{resp['id']}")

    # Update
    elif state == 'present':
        # Check if password should be updated
        if nac and 'supplicant' in nac:
            if not nac['supplicant'].get('password_update'):
                nac['supplicant']['password'] = current_eth['_8021X']['supplicant']['password']
            del nac['supplicant']['password_update']

        update_eth = conn.update_dict(current_eth,
                                      description=description,
                                      type=type,
                                      _8021X=nac,
                                      )

        if update_eth:
            result['changed'] = True
            if not module.check_mode:
                conn.patch(f"rkszones/{zone['id']}/profile/ethernetPort/{current_eth['id']}", payload=update_eth)
                new_eth = conn.get(f"rkszones/{zone['id']}/profile/ethernetPort/{current_eth['id']}")
            else:
                new_eth = copy.deepcopy(current_eth)
                new_eth.update(update_eth)
            result['eth'] = new_eth

    # Delete
    elif current_eth is not None and state == 'absent':
        result['changed'] = True
        result['eth'] = None
        if not module.check_mode:
            conn.delete(f"rkszones/{zone['id']}/profile/ethernetPort/{current_eth['id']}")
        new_eth = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_eth,
            after=new_eth,
        )
    module.exit_json(**result)


if __name__ == '__main__':
    main()
