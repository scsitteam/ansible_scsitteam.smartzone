#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: sz_certstore_cert_info

short_description: Manage Trusted CAs

description: Manage trusted cas and chains.

options:
    name:
        description: Name of the Cert to query.
        required: True
        type: str

author:
    - Marius Rieder (@jiuka)
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')

    # Get Current Cert
    for cert in conn.retrive_list('certstore/certificate'):
        if cert['name'] == name:
            result['cert'] = cert
    result['yolo'] = list(conn.retrive_list('certstore/certificate'))
    result['name'] = name

    module.exit_json(**result)


if __name__ == '__main__':
    main()
