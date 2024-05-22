#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ap_registration

short_description: Manage AP registration rules

description: Manage AP registration rules

options:
    description:
        description: Rule description. Use to identify the rule to manage.
        type: str
        required: true
    zone:
        description: Zone to add aps to
        type: str
        required: true
    ip_range:
        description: Match aps by ip range
        type: dict
        suboptions:
            from_ip:
                description: Range start ip
                type: str
                required: true
                aliases: [from]
            to_ip:
                description: Range start ip
                type: str
                required: true
                aliases: [to]
    subnet:
        description: Match aps by subnet
        type: dict
        suboptions:
            network:
                description: Subnet network address
                type: str
                required: true
            mask:
                description: Subnet mask
                type: str
                required: true
    gps:
        description: Match aps by gps location
        type: dict
        suboptions:
            latitude:
                description: GPS latitude
                type: int
                required: true
                aliases: [lat]
            longitude:
                description: GPS longitude
                type: int
                required: true
                aliases: [lon]
            distance:
                description: Distance
                type: int
                required: true
                aliases: [d]
    tag:
        description: Match aps by tag
        type: str
    state:
        description: State of the syslog profile.
        type: str
        default: present
        choices: [present, absent]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Ensure AP Registration Rule
  ap_registration:
    description: Ansible
    zone: Ansible
    subnet:
      network: 192.168.1.0
      mask: 255.255.255.0
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        description=dict(type='str', required=True),
        zone=dict(type='str', required=True),
        ip_range=dict(type='dict', options=dict(
            from_ip=dict(type='str', required=True, aliases=['from']),
            to_ip=dict(type='str', required=True, aliases=['to']),
        )),
        subnet=dict(type='dict', options=dict(
            network=dict(type='str', required=True),
            mask=dict(type='str', required=True),
        )),
        gps=dict(type='dict', options=dict(
            latitude=dict(type='int', required=True, aliases=['lat']),
            longitude=dict(type='int', required=True, aliases=['lon']),
            distance=dict(type='int', required=True, aliases=['d']),
        )),
        tag=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('ip_range', 'subnet', 'gps', 'tag'),
        ],
        required_if=[
            ('state', 'present', ('ip_range', 'subnet', 'gps', 'tag'), True),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    description = module.params.get('description')
    ip_range = module.params.get('ip_range')
    subnet = module.params.get('subnet')
    gps = module.params.get('gps')
    tag = module.params.get('tag')
    state = module.params.get('state')

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone)

    # Get current group
    current_rule = None
    for rule in conn.get('apRules')['list']:
        if rule['description'] == description:
            current_rule = conn.get(f"apRules/{rule['id']}")
    result['current_rule'] = current_rule
    result['zone'] = (zone['id'], zone['name'])

    # Create
    if current_rule is None and state == 'present':
        new_rule = dict(
            description=description,
            mobilityZone=dict(
                id=zone['id'],
                name=zone['name']
            )
        )
        if ip_range:
            new_rule.update(dict(
                type='IPAddressRange',
                ipAddressRange=dict(
                    fromIp=ip_range['from_ip'],
                    toIp=ip_range['to_ip'],
                )
            ))
        elif subnet:
            new_rule.update(dict(
                type='Subnet',
                subnet=dict(
                    networkAddress=subnet['network'],
                    subnetMask=subnet['mask'],
                )
            ))
        elif gps:
            new_rule.update(dict(
                type='GPSCoordinates',
                gpsCoordinates=dict(
                    latitude=gps['latitude'],
                    longitude=gps['longitude'],
                    distance=gps['distance'],
                )
            ))
        elif tag:
            new_rule.update(dict(
                type='ProvisionTag',
                provisionTag=tag,
            ))

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('apRules', payload=new_rule)
            new_rule = conn.get(f"apRules/{resp['id']}")

    # Update
    elif state == 'present':
        update_rule = dict()
        if current_rule['mobilityZone']['id'] != zone['id']:
            update_rule['mobilityZone'] = dict(
                id=zone['id'],
                name=zone['name']
            )
        if ip_range and (
            current_rule.get('ipAddressRange', {}).get('fromIp') != ip_range['from_ip']
            or current_rule.get('ipAddressRange', {}).get('toIp') != ip_range['to_ip']
        ):
            update_rule.update(dict(
                type='IPAddressRange',
                ipAddressRange=dict(
                    fromIp=ip_range['from_ip'],
                    toIp=ip_range['to_ip'],
                )
            ))
        elif subnet and (
            current_rule['subnet'] is None
            or current_rule['subnet'].get('networkAddress') != subnet['network']
            or current_rule['subnet'].get('subnetMask') != subnet['mask']
        ):
            update_rule.update(dict(
                type='Subnet',
                subnet=dict(
                    networkAddress=subnet['network'],
                    subnetMask=subnet['mask'],
                )
            ))
        elif gps and (
            current_rule['gpsCoordinates'] is None
            or current_rule['gpsCoordinates'].get('latitude') != gps['latitude']
            or current_rule['gpsCoordinates'].get('longitude') != gps['longitude']
            or current_rule['gpsCoordinates'].get('distance') != gps['distance']
        ):
            update_rule.update(dict(
                type='GPSCoordinates',
                gpsCoordinates=dict(
                    latitude=gps['latitude'],
                    longitude=gps['longitude'],
                    distance=gps['distance'],
                )
            ))
        elif tag and current_rule.get('gpsCoordinates') != tag:
            update_rule.update(dict(
                type='ProvisionTag',
                provisionTag=tag,
            ))

        if update_rule:
            result['changed'] = True
            if not module.check_mode:
                conn.patch(f"apRules/{current_rule['id']}", payload=update_rule)
                new_rule = conn.get(f"apRules/{current_rule['id']}")
            else:
                new_rule = copy.deepcopy(current_rule)
                new_rule.update(update_rule)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_rule,
            after=new_rule,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
