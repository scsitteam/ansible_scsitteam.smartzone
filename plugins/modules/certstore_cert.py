#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: certstore_cert

short_description: Manage x509 certificates.

description: Manage x509 certificates and keys.

options:
    name:
        description: Name of the cert/key to manage
        required: True
        type: str
    description:
        description: Description of the cert/key
        type: str
    cert:
        description: PEM represenation of the cert.
        type: str
    key:
        description: PEM represenation of the key.
        type: str
    passphrase:
        description: Passphrace of the PEM key.
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
- name: Choose passphrase
  ansible.builtin.set_fact:
  passphrase: "{{ lookup('ansible.builtin.password', '/dev/null') }}"

- name: Generate Privatkey
  community.crypto.openssl_privatekey_pipe:
    type: RSA
    cipher: auto
    passphrase: "{{ passphrase }}"
    diff: false
    no_log: true
    register: key

- name: Generate CSR
  community.crypto.openssl_csr_pipe:
    privatekey_content: "{{ key.privatekey }}"
    privatekey_passphrase: "{{ passphrase }}"
    common_name: smartzone.examlpe.com
    organization_name: Ansible
    subject_alt_name:
        - "DNS:smartzone.examlpe.com"
    register: csr

- name: Generate SelfSigned Certificate
  community.crypto.x509_certificate_pipe:
    provider: selfsigned
    privatekey_content: "{{ key.privatekey }}"
    privatekey_passphrase: "{{ passphrase }}"
    csr_content: "{{ csr.csr }}"
  register: cert

- name: Upload Cert and key
  certstore_cert:
    name: smartzone.examlpe.com
    cert: "{{ cert.certificate }}"
    key: "{{ key.privatekey }}"
    passphrase: "{{ passphrase }}"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        cert=dict(type='str'),
        key=dict(type='str', no_log=True),
        passphrase=dict(type='str', no_log=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('cert', 'key'), False),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    description = module.params.get('description')
    cert = module.params.get('cert')
    key = module.params.get('key')
    passphrase = module.params.get('passphrase')
    state = module.params.get('state')

    # Get current state
    current_cert = None
    for cert in conn.retrive_list('certstore/certificate'):
        if cert['name'] == name:
            current_cert = cert
            result['cert'] = current_cert

    # Create
    if current_cert is None and state == 'present':
        payload = dict(
            name=name,
            data=cert,
            privateKeyData=key,
        )
        if description:
            payload['description'] = description
        if passphrase:
            payload['passphrase'] = passphrase

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('certstore/certificate', json=payload)
            new_cert = conn.get(f"certstore/certificate/{resp['id']}")
        else:
            new_cert = payload
        result['cert'] = new_cert

    # Delete
    elif state == 'absent':
        result['changed'] = True
        if not module.check_mode:
            resp = conn.delete(f"certstore/certificate/{current_cert['id']}")
        new_cert = None

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_cert,
            after=new_cert,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
