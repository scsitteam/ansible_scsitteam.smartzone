#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: wlan

short_description: Manage WLANs

description: Manage WLANs

options:
    zone:
        description: Zone to manage wlan group in
        type: str
        required: true
    name:
        description: Wlan group name
        type: str
        required: true
    ssid:
        description: Wlan SSID
        type: str
    type:
        description: Wlan Type
        type: str
        choices: [
            Standard_Open, Standard_8021X, Standard_Mac, Hotspot, Hotspot_MacByPass,
            Guest, WebAuth, Hotspot20, Hotspot20_Open, Hotspot20_OSEN
        ]
    groups:
        description: Wlan group membership
        type: dict
        suboptions:
            add:
                description: Groups to add
                type: list
                elements: str
                default: []
            remove:
                description: Groups to remove
                type: list
                elements: str
                default: []
            set:
                description: Groups to set
                type: list
                elements: str
                default: []
    wpa2:
        description: WPA2 configuration
        type: dict
        suboptions:
            algorithm:
                description: WPA algorithm
                type: str
                default: AES
                choices: [AES, TKIP_AES, AES_GCMP_256]
            passphrase:
                description: WPA PSK passphrase
                type: str
            passphrase_update:
                description: Update WPA PSK passphrase
                type: bool
                default: True
            fast_roaming:
                description: Enable fast roaming (802.11r)
                type: bool
                default: False
            mfp:
                description: Management Frame Protection (802.11w)
                type: str
                default: disabled
                choices: [disabled, capable, required]
            reserve_ssid:
                description: Enable reserve SSID mode
                type: bool
                default: False
    wpa23:
        description: WPA2/3 configuration
        type: dict
        suboptions:
            algorithm:
                description: WPA algorithm
                type: str
                default: AES
                choices: [AES, AUTO, AES_GCMP_256]
            passphrase:
                description: WPA2 PSK passphrase
                type: str
            passphrase_update:
                description: Update WPA2 PSK passphrase
                type: bool
                default: True
            sae_passphrase:
                description: WPA3 PSK passphrase
                type: str
            sae_passphrase_update:
                description: Update WPA3 PSK passphrase
                type: bool
                default: True
            fast_roaming:
                description: Enable fast roaming (802.11r)
                type: bool
                default: False
            mfp:
                description: Management Frame Protection (802.11w)
                type: str
                default: capable
                choices: [disabled, capable, required]
            reserve_ssid:
                description: Enable reserve SSID mode
                type: bool
                default: False
            transition_disable:
                description: transition to mose secure mode
                type: bool
                default: True
    wpa3:
        description: WPA3 configuration
        type: dict
        suboptions:
            algorithm:
                description: WPA algorithm
                type: str
                default: AES
                choices: [AES, AUTO, AES_GCMP_256]
            sae_passphrase:
                description: WPA3 PSK passphrase
                type: str
            sae_passphrase_update:
                description: Update WPA3 PSK passphrase
                type: bool
                default: True
            fast_roaming:
                description: Enable fast roaming (802.11r)
                type: bool
                default: False
            mfp:
                description: Management Frame Protection (802.11w)
                type: str
                default: required
                choices: [disabled, capable, required]
            reserve_ssid:
                description: Enable reserve SSID mode
                type: bool
                default: False
    auth_profile:
        description: Authentication profile
        type: dict
        suboptions:
            profile:
                description: Authentication profile to use
                type: str
                required: True
            proxy:
                description: proxy authentication thgrouh smartzone
                type: bool
                default: False
    radius_options:
        description: Radius options
        type: dict
        suboptions:
            nas_id:
                description: NAS ID selection
                type: str
                choices: [WLAN_BSSID, AP_MAC, Customized]
            customized_nas_id:
                description: Custom NAS ID
                type: str
    vlan:
        description: VLan access configuration
        type: dict
        suboptions:
            accessVlan:
                description: Access VLan to use
                type: int
    dpsk:
        description: Dynamic PSK configuration
        type: dict
        suboptions:
            state:
                description: D-PSK state
                type: str
                default: disabled
                choices: [enabled, disabled]
            length:
                description: D-PSK length
                type: int
                default: 62
            type:
                description: D-PSK secret type
                type: str
                default: Secure
                choices: [Secure, KeyboardFriendly, NumbersOnly]
            expiration:
                description: D-PSK expiration period
                type: str
                default: Unlimited
                choices: [Unlimited, OneDay, TwoDays, OneWeek, TwoWeeks, OneMonth, SixMonths, OneYear, TwoYears]
            expiration_type:
                description: D-PSK expiration start
                type: str
                default: CreateTime
                choices: [CreateTime, FirstUse]
    advanced:
        description: Advanced wlan option
        type: dict
        suboptions:
            hide:
                description: Hide the SSID
                type: bool
            client_isolation:
                description: Indicates whether wireless client isolation is enabled or disabled.
                type: bool
            client_isolation_unicast:
                description: Indicates whether isolate unicast of wireless client isolation is enabled or disabled.
                type: bool
            client_isolation_multicast:
                description: Indicates whether isolate multicast of wireless client isolation is enabled or disabled.
                type: bool
            client_isolation_auto_vrrp:
                description: Indicates whether Automatic support for VRRP of wireless client isolation is enabled or disabled.
                type: bool
    state:
        description: Desired state of the ap group
        type: str
        default: present
        choices: ['present', 'absent']

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup SSID Ansible
  wlan:
    zone: Ansible
    name: Ansible-WPA2
    ssid: Ansible
    type: Standard_Open
    wpa2:
      passphrase: Ansible
    vlan:
      accessVlan: 123
    groups:
      set:
        - 2G
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def build_encryption_dict(params):
    encryption = None
    if params.get('wpa2'):
        encryption = params.get('wpa2')
        encryption['method'] = 'WPA2'
    elif params.get('wpa23'):
        encryption = params.get('wpa23')
        encryption['method'] = 'WPA23_Mixed'
    elif params.get('wpa3'):
        encryption = params.get('wpa3')
        encryption['method'] = 'WPA3'

    for old, new in [
        ('fast_roaming', 'support80211rEnabled'),
        ('sae_passphrase', 'saePassphrase'), ('sae_passphrase_update', 'saePassphrase_update'),
        ('reserve_ssid', 'reserveSsidEnabled'),
        ('transition_disable', 'transitionDisable')
    ]:
        if encryption and old in encryption:
            encryption[new] = encryption[old]
            del encryption[old]

    return encryption


def build_dpsk_dict(params):
    dpsk = params.get('dpsk')

    if not dpsk:
        return None
    dpsk['dpskEnabled'] = dpsk['state'] == 'enabled'
    del dpsk['state']

    for old, new in [
        ('type', 'dpskType'),
        ('expiration_type', 'dpskFromType'),
    ]:
        if old in dpsk:
            dpsk[new] = dpsk[old]
            del dpsk[old]

    return dpsk


def build_radius_options_dict(params):
    options = params.get('radius_options')

    if not options:
        return None

    radius_options = dict()

    for src, dst in [
        ('nas_id', 'nasIdType'),
        ('customized_nas_id', 'customizedNasId'),
    ]:
        if src in options and options[src]:
            radius_options[dst] = options[src]

    return radius_options


def build_advanced_options_dict(params):
    options = params.get('advanced')

    if not options:
        return None

    advanced_options = dict()

    for src, dst in [
        ('hide', 'hideSsidEnabled'),
        ('client_isolation', 'clientIsolationEnabled'),
        ('client_isolation_unicast', 'clientIsolationUnicastEnabled'),
        ('client_isolation_multicast', 'clientIsolationMulticastEnabled'),
        ('client_isolation_auto_vrrp', 'clientIsolationAutoVrrpEnabled'),
    ]:
        if src in options and options[src] is not None:
            advanced_options[dst] = options[src]

    return advanced_options


def main():
    argument_spec = dict(
        zone=dict(type='str', required=True),
        name=dict(type='str', required=True),
        ssid=dict(type='str'),
        type=dict(type='str', choices=[
            "Standard_Open", "Standard_8021X", "Standard_Mac", "Hotspot", "Hotspot_MacByPass",
            "Guest", "WebAuth", "Hotspot20", "Hotspot20_Open", "Hotspot20_OSEN"
        ]),
        groups=dict(type='dict', default=None, options=dict(
            add=dict(type='list', default=[], elements='str'),
            remove=dict(type='list', default=[], elements='str'),
            set=dict(type='list', default=[], elements='str'),
        )),
        # Encryption
        wpa2=dict(type='dict', options=dict(
            algorithm=dict(type='str', default='AES', choices=["AES", "TKIP_AES", "AES_GCMP_256"]),
            passphrase=dict(type='str', no_log=True),
            passphrase_update=dict(type='bool', default=True, no_log=False),
            fast_roaming=dict(type='bool', default=False),
            mfp=dict(type='str', default='disabled', choices=["disabled", "capable", "required"]),
            reserve_ssid=dict(type='bool', default=False),
        )),
        wpa23=dict(type='dict', options=dict(
            algorithm=dict(type='str', default='AES', choices=["AES", "AUTO", "AES_GCMP_256"]),
            passphrase=dict(type='str', no_log=True),
            passphrase_update=dict(type='bool', default=True, no_log=False),
            sae_passphrase=dict(type='str', no_log=True),
            sae_passphrase_update=dict(type='bool', default=True, no_log=False),
            fast_roaming=dict(type='bool', default=False),
            mfp=dict(type='str', default='capable', choices=["disabled", "capable", "required"]),
            reserve_ssid=dict(type='bool', default=False),
            transition_disable=dict(type='bool', default=True)
        )),
        wpa3=dict(type='dict', options=dict(
            algorithm=dict(type='str', default='AES', choices=["AES", "AUTO", "AES_GCMP_256"]),
            sae_passphrase=dict(type='str', no_log=True),
            sae_passphrase_update=dict(type='bool', default=True, no_log=False),
            fast_roaming=dict(type='bool', default=False),
            mfp=dict(type='str', default='required', choices=["disabled", "capable", "required"]),
            reserve_ssid=dict(type='bool', default=False),
        )),
        auth_profile=dict(type='dict', default=None, options=dict(
            profile=dict(type='str', required=True),
            proxy=dict(type='bool', default=False),
        )),
        radius_options=dict(
            type='dict',
            options=dict(
                nas_id=dict(type='str', choices=["WLAN_BSSID", "AP_MAC", "Customized"]),
                customized_nas_id=dict(type='str')
            ),
            required_if=[
                ('nas_id', 'Customized', ('customized_nas_id',)),
            ],
        ),
        vlan=dict(type='dict', default=None, options=dict(
            accessVlan=dict(type='int'),
        )),
        dpsk=dict(type='dict', default=None, options=dict(
            state=dict(type='str', default='disabled', choices=['enabled', 'disabled']),
            length=dict(type='int', default=62),
            type=dict(type='str', default='Secure', choices=['Secure', 'KeyboardFriendly', 'NumbersOnly']),
            expiration=dict(type='str', default='Unlimited', choices=[
                'Unlimited', 'OneDay', 'TwoDays', 'OneWeek', 'TwoWeeks',
                'OneMonth', 'SixMonths', 'OneYear', 'TwoYears'
            ]),
            expiration_type=dict(type='str', default='CreateTime', choices=['CreateTime', 'FirstUse']),
        )),
        advanced=dict(type='dict', options=dict(
            hide=dict(type='bool'),
            client_isolation=dict(type='bool'),
            client_isolation_unicast=dict(type='bool'),
            client_isolation_multicast=dict(type='bool'),
            client_isolation_auto_vrrp=dict(type='bool'),
        )),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('ssid', 'type')),
            ('type', 'Standard_8021X', ('auth_profile',)),
        ],
        mutually_exclusive=[
            ('wpa2', 'wpa23', 'wpa3'),
        ],
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    zone = module.params.get('zone')
    name = module.params.get('name')
    ssid = module.params.get('ssid')
    type = module.params.get('type')
    groups = module.params.get('groups')
    state = module.params.get('state')
    encryption = build_encryption_dict(module.params)
    vlan = module.params.get('vlan')
    dpsk = build_dpsk_dict(module.params)
    radius_options = build_radius_options_dict(module.params)
    advanced_options = build_advanced_options_dict(module.params)

    # Resolve Zone
    zone = conn.retrive_by_name('rkszones', zone, required=True)

    # Resolve Auth Profile
    auth_profile = module.params.get('auth_profile')
    if auth_profile:
        profile = conn.retrive_by_name(f"rkszones/{zone['id']}/aaa/radius", auth_profile['profile'])
        auth_profile = dict(
            throughController=auth_profile['proxy'],
            id=profile['id'],
            name=profile['name'],
            authenticationOption=None
        )

    # Get current group
    current_wlan = conn.retrive_by_name(f"rkszones/{zone['id']}/wlans", name)
    new_wlan = None

    # Create
    if current_wlan is None and state == 'present':
        new_wlan = dict(
            name=name,
            ssid=ssid,
        )
        if encryption:
            new_wlan['encryption'] = {
                key: value
                for key, value in encryption.items()
                if value is not None and not key.endswith('_update')
            }
        if advanced_options:
            new_wlan['advancedOptions'] = advanced_options

        if type == 'Standard_Open':
            ressource = f"rkszones/{zone['id']}/wlans"
        elif type == 'Standard_8021X':
            ressource = f"rkszones/{zone['id']}/wlans/standard8021X"
            new_wlan['authServiceOrProfile'] = auth_profile
        else:
            module.fail_json(mfs=f"Creation of type {type} not suported", **result)

        if vlan:
            new_wlan['vlan'] = vlan
        if dpsk:
            new_wlan['dpsk'] = dpsk

        result['changed'] = True
        result['wlan'] = new_wlan
        if not module.check_mode:
            resp = conn.post(ressource, payload=new_wlan)
            new_wlan = conn.get(f"rkszones/{zone['id']}/wlans/{resp['id']}")

    # Update
    elif state == 'present':
        update_wlan = dict()
        if ssid and current_wlan['ssid'] != ssid:
            update_wlan['ssid'] = ssid
        if encryption and any(
            current_wlan['encryption'].get(key) != encryption[key]
            for key in encryption
            if not key.endswith('_update') and encryption.get(f"{key}_update", True)
        ):
            update_wlan['encryption'] = {
                key: current_wlan['encryption'][key]
                for key in current_wlan['encryption']
                if current_wlan['encryption'][key] is not None
            }
            update_wlan['encryption'].update({
                key: value
                for key, value in encryption.items()
                if value is not None and not key.endswith('_update') and encryption.get(f"{key}_update", True)
            })
        if vlan and current_wlan['vlan']['accessVlan'] != vlan['accessVlan']:
            update_wlan['vlan'] = vlan
        if dpsk and any(current_wlan['dpsk'].get(key) != dpsk[key] for key in dpsk):
            update_wlan['dpsk'] = dpsk
        if radius_options and any(current_wlan['radiusOptions'].get(key) != value for key, value in radius_options.items()):
            update_wlan['radiusOptions'] = radius_options
        if advanced_options and any(current_wlan['advancedOptions'].get(key) != value for key, value in advanced_options.items()):
            update_wlan['advancedOptions'] = advanced_options

        if update_wlan:
            result['changed'] = True
            if not module.check_mode:
                conn.patch(f"rkszones/{zone['id']}/wlans/{current_wlan['id']}", payload=update_wlan)
                new_wlan = conn.get(f"rkszones/{zone['id']}/wlans/{current_wlan['id']}")
            else:
                new_wlan = copy.deepcopy(current_wlan)
                new_wlan.update(update_wlan)

    # Delete
    elif current_wlan is not None and state == 'absent':
        result['changed'] = True
        new_wlan = None
        if not module.check_mode:
            conn.delete(f"rkszones/{zone['id']}/wlans/{current_wlan['id']}")

    # Ensure Groups
    if groups and state == 'present':
        wlan = current_wlan or new_wlan
        if 'id' in wlan:
            current_groups = conn.retrive_groups_by_wlan(wlan)
            if current_wlan:
                current_wlan['groups'] = [g['name'] for g in current_groups]
            if not new_wlan:
                new_wlan = copy.deepcopy(current_wlan)
            else:
                new_wlan['groups'] = [g['name'] for g in current_groups]
            result['groups'] = current_groups

            if groups['set']:
                groups['add'] = groups['set']
                groups['remove'] = [g['name'] for g in current_groups if g['name'] not in groups['set']]

            for group in groups['add']:
                group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", group, required=True)
                if not any(g['id'] == group['id'] for g in current_groups):
                    result['changed'] = True
                    new_wlan['groups'].append(group['name'])
                    if not module.check_mode:
                        conn.post(f"rkszones/{zone['id']}/wlangroups/{group['id']}/members", payload=dict(id=wlan['id']))

            for group in groups['remove']:
                group = conn.retrive_by_name(f"rkszones/{zone['id']}/wlangroups", group)
                if group and any(g['id'] == group['id'] for g in current_groups):
                    result['changed'] = True
                    new_wlan['groups'].remove(group['name'])
                    if not module.check_mode:
                        conn.delete(f"rkszones/{zone['id']}/wlangroups/{group['id']}/members/{wlan['id']}")

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_wlan,
            after=new_wlan,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
