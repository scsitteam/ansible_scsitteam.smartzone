#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: zone

short_description: Manage SmartZone zone

description: Manage SmartZone zone

options:
    name:
        description: Name of the zone to manage
        type: str
        required: true
    description:
        description: Description of the zone
        type: str
    ap_login_name:
        description: Login name for aps access.
        type: str
    ap_login_password:
        description: Password for aps access.
        type: str
    country_code:
        description: Country code for zone
        type: str
    timezone:
        description: Timezone for zone
        type: str
    syslog:
        description: Syslog profile for zone
        type: str
    snmp:
        description: SNMP profile for zone
        type: str
    smart_monitor_state:
        description: State of SmartMonitor to ensure
        type: str
        choices: [enabled, disabled]
    smart_monitor:
        description: SmartMonitor configuration
        type: dict
        suboptions:
            interval:
                description: SmartMonitor probe interval
                type: int
                required: True
            retry:
                description: SmartMonitor probe retry
                type: int
                required: True
    state:
        description: Desired state of the AD aaa server.
        type: str
        default: present
        choices: ['present', 'absent']

extends_documentation_fragment:
- scsitteam.smartzone.ap_basic_config.documentation

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Create Zones
  scsitteam.smartzone.zone:
    name: Ansible
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection
from ansible_collections.scsitteam.smartzone.plugins.module_utils.params import ApBasicConfig


def main():
    argument_spec = ApBasicConfig.argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        ap_login_name=dict(type='str'),
        ap_login_password=dict(type='str', no_log=True),
        country_code=dict(type='str'),
        timezone=dict(type='str'),
        syslog=dict(type='str'),
        snmp=dict(type='str'),
        smart_monitor_state=dict(type='str', choices=['enabled', 'disabled']),
        smart_monitor=dict(type='dict', options=dict(
            interval=dict(type='int', required=True),
            retry=dict(type='int', required=True),
        )),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('smart_monitor_state', 'enabled', ('smart_monitor',)),
        ],
        required_together=ApBasicConfig.required_together()
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    name = module.params.get('name')
    description = module.params.get('description')
    ap_login_name = module.params.get('ap_login_name')
    ap_login_password = module.params.get('ap_login_password')
    country_code = module.params.get('country_code')
    timezone = dict(customizedTimezone=None, systemTimezone=module.params.get('timezone')) if module.params.get('timezone') else None
    syslog = module.params.get('syslog')
    snmp = module.params.get('snmp')
    smart_monitor_state = module.params.get('smart_monitor_state')
    smart_monitor = module.params.get('smart_monitor')
    ap_basic_config = ApBasicConfig(module.params)
    state = module.params.get('state')

    # Resolve Syslog and SNMP to ID
    if syslog:
        profile = conn.retrive_by_name(f"apSyslogServerProfiles?domainId={conn.domainId}", syslog)
        syslog = dict(
            syslogConfigType='AP_SYSLOG_SERVER_PROFILE',
            syslogServerProfileId=profile['id']
        )
    if snmp:
        profile = conn.retrive_by_name(f"apSnmpAgentProfiles?domainId={conn.domainId}", snmp)
        snmp = dict(
            apSnmpEnabled=True,
            snmpConfigType='AP_SNMP_AGENT_PROFILE',
            apSnmpAgentProfileId=profile['id']
        )

    # Get current zone
    current_zone = conn.retrive_by_name('rkszones', name)

    # Create
    if current_zone is None and state == 'present':
        new_zone = dict(
            name=name,
            login=dict(apLoginName=ap_login_name, apLoginPassword=ap_login_password)
        )
        if description:
            new_zone['description'] = description
        if country_code:
            new_zone['countryCode'] = country_code
        if timezone:
            new_zone['timezone'] = timezone
        if syslog:
            new_zone['syslog'] = syslog
        if snmp:
            new_zone['snmpAgent'] = snmp
        if smart_monitor_state == 'enabled':
            new_zone['smartMonitor'] = dict(
                intervalInSec=smart_monitor['interval'],
                retryThreshold=smart_monitor['retry'],
            )
        ap_basic_config.update(new_zone)

        result['changed'] = True
        if not module.check_mode:
            resp = conn.post('rkszones', payload=new_zone)
            new_zone = conn.get(f"rkszones/{resp['id']}")

    # Update
    elif state == 'present':
        update_zone = dict()
        if description and current_zone['description'] != description:
            update_zone['description'] = description
        if country_code and current_zone['countryCode'] != country_code:
            update_zone['countryCode'] = country_code
        if timezone and current_zone['timezone'] != timezone:
            update_zone['timezone'] = timezone
        if syslog:
            for key in syslog:
                if current_zone['syslog'][key] != syslog[key]:
                    if 'syslog' not in update_zone:
                        update_zone['syslog'] = {}
                    update_zone['syslog'][key] = syslog[key]
        if snmp:
            for key in snmp:
                if current_zone['snmpAgent'][key] != snmp[key]:
                    if 'snmpAgent' not in update_zone:
                        update_zone['snmpAgent'] = {}
                    update_zone['snmpAgent'][key] = snmp[key]
        if smart_monitor_state == 'enabled' and (
            current_zone['smartMonitor'] is None
            or current_zone['smartMonitor'].get('intervalInSec') != smart_monitor['interval']
            or current_zone['smartMonitor'].get('retryThreshold') != smart_monitor['retry']
        ):
            update_zone['smartMonitor'] = dict(
                intervalInSec=smart_monitor['interval'],
                retryThreshold=smart_monitor['retry'],
            )
        elif smart_monitor_state == 'disabled' and current_zone['smartMonitor'] is not None:
            result['changed'] = True
            if not module.check_mode:
                conn.delete(f"rkszones/{current_zone['id']}/smartMonitor")
                new_zone = conn.get(f"rkszones/{current_zone['id']}")
            else:
                update_zone['smartMonitor'] = None
        ap_basic_config.update(update_zone, current_zone)

        if update_zone:
            result['changed'] = True
            if not module.check_mode:
                resp = conn.patch(f"rkszones/{current_zone['id']}", payload=update_zone)
                new_zone = conn.get(f"rkszones/{current_zone['id']}")
            else:
                new_zone = copy.deepcopy(current_zone)
                new_zone.update(update_zone)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_zone,
            after=new_zone,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
