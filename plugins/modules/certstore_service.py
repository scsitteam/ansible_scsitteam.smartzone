#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: sz_certstore_service

short_description: Manage Certs to use

description: Select certs for different services.

options:
    mgmt_web:
        description: Id of the Cert to use for management web.
        type: str
    ap_portal:
        description: Id of the Cert to use for ap portal.
        type: str
    hotspot:
        description: Id of the Cert to use for hotspot.
        type: str
    communicator:
        description: Id of the Cert to use for communicator.
        type: str

extends_documentation_fragment:
    - ruckus

author:
    - Marius Rieder (@jiuka)
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection

def main():
    argument_spec = dict(
        mgmt_web=dict(type='str'),
        ap_portal=dict(type='str'),
        hotspot=dict(type='str'),
        communicator=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    mgmt_web = module.params.get('mgmt_web')
    ap_portal = module.params.get('ap_portal')
    hotspot = module.params.get('hotspot')
    communicator = module.params.get('communicator')

    # Get current state
    current_scerts = {sc['service']:sc['certificate']  for sc in conn.get('certstore/setting')['serviceCertificates']}

    update_scerts = []
    if mgmt_web and current_scerts['MANAGEMENT_WEB']['id'] != mgmt_web:
        update_scerts.append(dict(
            service= "MANAGEMENT_WEB",
            certificate=dict(id=mgmt_web)
        ))
    if ap_portal and current_scerts['AP_PORTAL']['id'] != ap_portal:
        update_scerts.append(dict(
            service= "AP_PORTAL",
            certificate=dict(id=ap_portal)
        ))
    if hotspot and current_scerts['HOTSPOT']['id'] != hotspot:
        update_scerts.append(dict(
            service= "HOTSPOT",
            certificate=dict(id=hotspot)
        ))
    if communicator and current_scerts['COMMUNICATOR']['id'] != communicator:
        update_scerts.append(dict(
            service= "COMMUNICATOR",
            certificate=dict(id=communicator)
        ))

    if update_scerts:
        result['changed'] = True
        if not module.check_mode:
            conn.patch('certstore/setting/serviceCertificates', json=update_scerts)
            current_scerts = {sc['service']:sc['certificate']  for sc in conn.get('certstore/setting')['serviceCertificates']}
        else:
            new_scerts = copy.deepcopy(current_scerts)
            for sc in update_scerts:
                new_scerts[sc['service']] = sc['certificate']

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_scerts,
            after=new_scerts,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
