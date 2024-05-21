#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: certstore_trusted

short_description: Manage Trusted CAs

description: Manage trusted CAs and chains.

options:
    name:
        description: Name of the Trust Entry.
        required: True
        type: str
    description:
        description: Description of the Trust Entry.
        type: str
    root:
        description: Cert as PEM of the Trusted root CA. Required to create/update the entry.
        type: str
    intermediate:
        description: Cert as PEM of the intermidiate CAs.
        type: list
        elements: str
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure Trusted CA
  certstore_trusted:
    name: MYCA
    description: MYCA
    root: "{{ lookup('ansible.builtin.file', 'MYCA.crt') }}"
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        root=dict(type='str'),
        intermediate=dict(type='list', elements='str'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('root',), False),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    description = module.params.get('description')
    state = module.params.get('state')
    root = module.params.get('root')
    intermediate = module.params.get('intermediate')

    # Get Current Trust
    current_trust = conn.retrive_by_name('certstore/trustedCAChainCert', name)
    result['trusted'] = current_trust

    # Create
    if current_trust is None and state == 'present':
        payload = dict(
            name=name,
            rootCertData=root,
        )
        if description:
            payload['description'] = description
        if intermediate:
            payload['interCertData'] = intermediate

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('certstore/trustedCAChainCert', payload=payload)
            new_trust = conn.get(f"certstore/trustedCAChainCert/{resp['id']}")
        else:
            new_trust = payload
        result['trusted'] = new_trust

    # Update
    elif state == 'present':
        update_trust = dict()
        if description and current_trust['description'] != description:
            update_trust['description'] = description
        if current_trust['rootCertData'] != root:
            update_trust['rootCertData'] = root
        if intermediate is not None and current_trust['interCertData'] != intermediate:
            update_trust['interCertData'] = intermediate

        if update_trust:
            result['changed'] = True
            if not module.check_mode:
                resp = conn.patch(f"certstore/trustedCAChainCert/{current_trust['id']}", payload=update_trust)
                new_trust = conn.get(f"certstore/trustedCAChainCert/{current_trust['id']}")
            else:
                new_trust = copy.deepcopy(current_trust)
                new_trust.update(update_trust)
            result['trusted'] = new_trust

    # Delete
    elif current_trust is not None and state == 'absent':
        result['changed'] = True
        if not module.check_mode:
            conn.delete(f"certstore/trustedCAChainCert/{current_trust['id']}")
        new_trust = None
        del result['trusted']

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_trust,
            after=new_trust,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
