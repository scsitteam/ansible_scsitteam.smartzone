# -*- coding: utf-8 -*-

# Copyright (c) 2024, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import requests
from functools import cached_property
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection

class SmartZoneConnection(object):
    def __init__(self, module):
        self.module = module

    @cached_property
    def _cli(self):
        return Connection(self.module._socket_path)

    
    def get(self, ressource, expected_code=[200]):
        code , data = self._cli.send_request(ressource)
        if code not in expected_code:
            self.module.fail_json(msg=f"GET failed for '{ressource}'", status_code=code, body=data)
        return data
    
    def patch(self, ressource, payload, expected_code=[204]):
        code , data = self._cli.send_request(ressource, data=payload, method='PATCH')
        if code not in expected_code:
            self.module.fail_json(msg=f"PATCH failed for '{ressource}'", status_code=code, body=data)
        return data
    
    def put(self, ressource, payload, expected_code=[204]):
        code , data = self._cli.send_request(ressource, data=payload, method='PUT')
        if code not in expected_code:
            self.module.fail_json(msg=f"PUT failed for '{ressource}'", status_code=code, body=data)
        return data
    
    def post(self, ressource, payload, expected_code=[201]):
        code , data = self._cli.send_request(ressource, data=payload, method='POST')
        if code not in expected_code:
            self.module.fail_json(msg=f"POST failed for '{ressource}'", status_code=code, body=data)
        return data

    def delete(self, ressource, expected_code=[204]):
        code , data = self._cli.send_request(ressource, method='DELETE')
        if code not in expected_code:
            self.module.fail_json(msg=f"DELETE failed for '{ressource}'", status_code=code, body=data)
        return data

    def retrive_list(self, ressource, **kwargs):
        index = 0
        while True:
            page = self.get(ressource, **kwargs)
            for item in page['list']:
                yield item
            if not page['hasMore']:
                return
            index += len(item)

    def retrive_by_name(self, ressource, name, required=False, **kwargs):
        for item in self.retrive_list(ressource, **kwargs):
            if item['name'] == name:
                return self.get(f"{ressource}/{item['id']}")
        if required:
            self.module.fail_json(msg=f"Could not find ressource '{ressource}' with name '{name}'.") 
        return None
    
    def update_dict(self, current, **kwargs):
        return {
            key: kwargs[key]
            for key in kwargs
            if kwargs[key] is not None and current[key] != kwargs[key]
        }

    def retrive_groups_by_wlan(self, wlan):
        groups = []
        for item in self.retrive_list(f"rkszones/{wlan['zoneId']}/wlangroups"):
            if any(m['id'] == wlan['id'] for m in item['members']):
                groups.append(item)
        return groups
