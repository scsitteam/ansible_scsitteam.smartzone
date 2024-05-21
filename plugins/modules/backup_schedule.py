#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: backup_schedule

short_description: Manage SmartZone backup schedule

description: Manage SmartZone backup schedule

options:
    state:
        description: Enable or disable the automatic backup
        type: str
        default: enabled
        choices: [enabled, disabled]
    interval:
        description: Selects backup interval.
        type: str
        choices: [MONTHLY, WEEKLY, DAILY]
    hour:
        description: Hour to run the backup at.
        type: int
    minute:
        description: Munite to run the backup at.
        type: int
    day_of_week:
        description: Weekday to run weekly backups.
        type: str
        choices: [SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY]
    date_of_month:
        description: Day to run monthly backups.
        type: int

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Setup Backup
  backup_schedule:
    interval: DAILY
    hour: 3
    minute: 15
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        state=dict(type='str', default='enabled', choices=['enabled', 'disabled']),
        interval=dict(type='str', choices=['MONTHLY', 'WEEKLY', 'DAILY']),
        day_of_week=dict(type='str', choices=['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']),
        date_of_month=dict(type='int'),
        hour=dict(type='int'),
        minute=dict(type='int'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'enabled', ('hour', 'minute', 'interval'), False),
            ('interval', 'MONTHLY', ('date_of_month', ), False),
            ('interval', 'WEEKLY', ('day_of_week', ), False),
        ],
        mutually_exclusive=[
            ('date_of_month', 'day_of_week'),
        ]
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    state = module.params.get('state')
    interval = module.params.get('interval')
    hour = module.params.get('hour')
    minute = module.params.get('minute')
    date_of_month = module.params.get('date_of_month')
    day_of_week = module.params.get('day_of_week')

    # Get current schedule
    current_schedule = conn.get('configurationSettings/scheduleBackup')

    # Update
    update_schedule = dict()
    if current_schedule['enableScheduleBackup'] != (state == 'enabled'):
        update_schedule['enableScheduleBackup'] = (state == 'enabled')

    if state == 'enabled':
        if current_schedule['interval'] != interval:
            update_schedule['interval'] = interval
        if current_schedule['hour'] != hour:
            update_schedule['hour'] = hour
        if current_schedule['minute'] != minute:
            update_schedule['minute'] = minute
        if interval == 'WEEKLY' and current_schedule['dayOfWeek'] != day_of_week:
            update_schedule['dayOfWeek'] = day_of_week
        if interval == 'MONTHLY' and current_schedule['dateOfMonth'] != date_of_month:
            update_schedule['dateOfMonth'] = date_of_month

    if update_schedule:
        result['changed'] = True
        if not module.check_mode:
            conn.patch('configurationSettings/scheduleBackup', payload=update_schedule)
            new_schedule = conn.get('configurationSettings/scheduleBackup')
        else:
            new_schedule = copy.deepcopy(current_schedule)
            new_schedule.update(update_schedule)

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_schedule,
            after=new_schedule,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
