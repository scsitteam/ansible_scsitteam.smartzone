#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ap_autoapprove

short_description: Manage AP Auto approval setting

description: Manage AP Auto approval setting

options:
    state:
        description: Enable or Disable ap auto approve setting.
        type: str
        default: enabled
        choices: [enabled, disabled]

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Disable AP Autoapproval
  ap_autoapprove:
    state: disabled
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection


def main():
    argument_spec = dict(
        state=dict(type='str', default='enabled', choices=['enabled', 'disabled']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    conn = SmartZoneConnection(module)
    result = dict(changed=False)

    # Params
    state = (module.params.get('state') == 'enabled')

    # Get current state
    current_state = conn.get('system/apSettings/approval')

    # Update
    if current_state['approveEnabled'] != state:
        result['changed'] = True
        new_state = dict(approveEnabled=state)
        if not module.check_mode:
            conn.patch('system/apSettings/approval', payload=new_state)
            new_state = conn.get('system/apSettings/approval')

    # Diff
    if result['changed'] and module._diff:
        result['diff'] = dict(
            before=current_state,
            after=new_state,
        )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
