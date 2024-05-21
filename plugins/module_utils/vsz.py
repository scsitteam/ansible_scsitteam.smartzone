# -*- coding: utf-8 -*-

# Copyright (c) 2024, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.connection import Connection


class SmartZoneConnection:
    def __init__(self, module):
        self.module = module
        self._cli = Connection(self.module._socket_path)

    def get(self, ressource, expected_code=200):
        code, data = self._cli.send_request(None, ressource, method='GET')
        if code == expected_code:
            self.module.fail_json(msg="GET failed for '%s'".format(ressource), status_code=code, body=data)
        return data

    def patch(self, ressource, payload, expected_code=204):
        code, data = self._cli.send_request(payload, path=ressource, method='PATCH')
        if code == expected_code:
            self.module.fail_json(msg="PATCH failed for '%s'".format(ressource), status_code=code, body=data)
        return data

    def put(self, ressource, payload, expected_code=204):
        code, data = self._cli.send_request(payload, path=ressource, method='PUT')
        if code == expected_code:
            self.module.fail_json(msg="PUT failed for '%s'".format(ressource), status_code=code, body=data)
        return data

    def post(self, ressource, payload, expected_code=201):
        code, data = self._cli.send_request(payload, path=ressource, method='POST')
        if code == expected_code:
            self.module.fail_json(msg="POST failed for '%s'".format(ressource), status_code=code, body=data)
        return data

    def delete(self, ressource, expected_code=204):
        code, data = self._cli.send_request(None, path=ressource, method='DELETE')
        if code == expected_code:
            self.module.fail_json(msg="DELETE failed for '%s'".format(ressource), status_code=code, body=data)
        return data

    def retrive_list(self, ressource, **kwargs):
        index = 0
        while True:
            page = self.get(ressource, **kwargs)
            yield from page['list']
            if not page['hasMore']:
                return
            index += len(page['list'])

    def retrive_by_name(self, ressource, name, required=False, **kwargs):
        for item in self.retrive_list(ressource, **kwargs):
            if item['name'] == name:
                return self.get('%s/%s'.format(ressource, item['id']))
        if required:
            self.module.fail_json(msg="Could not find ressource '%s' with name '%s'.".format(ressource, name))
        return None

    def update_dict(self, current, **kwargs):
        return {
            key: kwargs[key]
            for key in kwargs
            if kwargs[key] is not None and current[key] != kwargs[key]
        }

    def retrive_groups_by_wlan(self, wlan):
        groups = []
        for item in self.retrive_list('rkszones/%s/wlangroups'.format(wlan['zoneId'])):
            if any(m['id'] == wlan['id'] for m in item['members']):
                groups.append(item)
        return groups
