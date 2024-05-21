#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adminaaa_ad

short_description: Manage AD AAA Server for the admin realm

description: Manage AD servers for SmartZone admin autentication.

options:
    name:
        description: Name of the Cert to query.
        required: True
        type: str
    realm:
        description: Realm to use the AD server for
        type: str
    ip:
        description: IP Address of the AD Server
        type: str
    port:
        description: Port to connect to
        type: int
    domain_name:
        description: AD Domain name
        type: str
    tls:
        description: Use TLS for LDAP connection to AD server
        type: bool
        default: False
    cn_identity:
        description: CN to compare x509 server certificate with.
        type: str
    proxy_user:
        description: AD bind user.
        type: str
    proxy_password:
        description: AD bind password.
        type: str
    proxy_password_update:
        description: Wheter to update the proxy_password.
        type: bool
        default: false
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup AD Server
  scsitteam.smartzone.adminaaa_ad:
    name: ad01
    ip: 192.168.0.1
    realm: contoso.com
    domain_name: contoso.com


- name: Remove AD Server
  scsitteam.smartzone.adminaaa_ad:
    name: ad01
    state: absent
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        realm=dict(type='str'),
        ip=dict(type='str'),
        port=dict(type='int'),
        domain_name=dict(type='str'),
        tls=dict(type='bool', default=False),
        cn_identity=dict(type='str'),
        proxy_user=dict(type='str'),
        proxy_password=dict(type='str', no_log=True),
        proxy_password_update=dict(type='bool', default=False, no_log=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('realm', 'ip', 'port', 'domain_name'), False),
            ('tls', True, ('cn_identity',)),
        ],
        required_together=[
            ('proxy_user', 'proxy_password'),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    state = module.params.get('state')
    realm = module.params.get('realm')
    ip = module.params.get('ip')
    port = module.params.get('port')
    domain_name = module.params.get('domain_name')
    tls = module.params.get('tls')
    cn_identity = module.params.get('cn_identity')
    proxy_user = module.params.get('proxy_user')
    proxy_password = module.params.get('proxy_password')
    proxy_password_update = module.params.get('proxy_password_update')

    # Seach Current Admin AAA Server
    current_aaa = conn.retrive_by_name('adminaaa?type=AD', name)

    # Create
    if current_aaa is None and state == 'present':
        result['changed'] = True
        new_aaa = dict(
            name=name,
            type='AD',
            activeDirectoryServer=dict(
                realm=realm,
                ip=ip,
                port=port,
                windowsDomainName=domain_name,
                tlsEnabled=tls
            )
        )
        if tls:
            new_aaa['activeDirectoryServer']['cnIdentity'] = cn_identity
        if proxy_user:
            new_aaa['activeDirectoryServer']['proxyUserPrincipalName'] = proxy_user
            new_aaa['activeDirectoryServer']['proxyUserPassword'] = proxy_password
        if not module.check_mode:
            resp = conn.post('adminaaa', payload=new_aaa)
            new_aaa = conn.get(f"adminaaa/{resp['id']}")
    # Update
    elif state == 'present':
        new_ad = dict()
        if current_aaa['activeDirectoryServer']['realm'] != realm:
            new_ad['realm'] = realm
        if current_aaa['activeDirectoryServer']['ip'] != ip:
            new_ad['ip'] = ip
        if current_aaa['activeDirectoryServer']['port'] != port:
            new_ad['port'] = port
        if current_aaa['activeDirectoryServer']['windowsDomainName'] != domain_name:
            new_ad['windowsDomainName'] = domain_name
        if current_aaa['activeDirectoryServer']['tlsEnabled'] != tls:
            new_ad['tlsEnabled'] = tls
        if tls and current_aaa['activeDirectoryServer']['cnIdentity'] != cn_identity:
            new_ad['cnIdentity'] = cn_identity
        if proxy_user and current_aaa['activeDirectoryServer'].get('proxyUserPrincipalName') != proxy_user:
            new_ad['proxyUserPrincipalName'] = proxy_user
        if proxy_password and proxy_password_update:
            new_ad['proxyUserPassword'] = proxy_password

        if new_ad:
            result['zzz'] = copy.deepcopy(new_ad)
            for key in current_aaa['activeDirectoryServer']:
                if key not in new_ad:
                    new_ad[key] = current_aaa['activeDirectoryServer'][key]

            result['changed'] = True
            if not module.check_mode:
                conn.put(f"adminaaa/{current_aaa['id']}", payload=dict(name=name, type='AD', activeDirectoryServer=new_ad))
                new_aaa = conn.get(f"adminaaa/{current_aaa['id']}")
            else:
                new_aaa = copy.deepcopy(current_aaa)
                new_aaa['activeDirectoryServer'].update(new_ad)

    # Delete
    elif current_aaa and state == 'absent':
        conn.delete(f"adminaaa/{current_aaa['id']}")
        new_aaa = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(before=current_aaa, after=new_aaa)

    module.exit_json(**result, current_aaa=current_aaa)


if __name__ == '__main__':
    main()
