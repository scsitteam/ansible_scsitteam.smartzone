# -*- coding: utf-8 -*-

# Copyright (c) 2024, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.connection import Connection


class ApBasicConfig:
    @staticmethod
    def argument_spec():
        return dict(
            location=dict(type='str'),
            location_additional=dict(type='str'),
            latitude=dict(type='float'),
            longitude=dict(type='float'),
            altitude=dict(type='dict', options=dict(
                value=dict(type='int'),
                unit=dict(type='str', default='meters', choices=['meters', 'floor'])
            )),
        )

    @staticmethod
    def required_together():
        return [
            ('latitude', 'longitude'),
        ]

    @staticmethod
    def to_dict(params):
        apconfig = dict()
        if params.get('location') is not None:
            apconfig['location'] = params.get('location')
        if params.get('location_additional') is not None:
            apconfig['locationAdditionalInfo'] = params.get('location_additional')
        if params.get('latitude') is not None:
            apconfig['latitude'] = params.get('latitude')
        if params.get('longitude') is not None:
            apconfig['longitude'] = params.get('longitude')
        if params.get('altitude') and params['altitude']['value'] is not None:
            apconfig['altitude'] = dict(
                altitudeUnit=params['altitude']['unit'],
                altitudeValue=params['altitude']['value'],
            )
        return apconfig

    @staticmethod
    def update_dict(current):
        update = dict()
        for key, value in current.items():
            if value is not None and current[key] != value:
                update[key] != value
        return update


class SmartZoneConnection:
    def __init__(self, module):
        self.module = module
        self._cli = Connection(self.module._socket_path)

    def get(self, ressource, expected_code=200):
        code, data = self._cli.send_request(None, ressource, method='GET')
        if code != expected_code:
            self.module.fail_json(msg=f"GET failed for '{ressource}'", status_code=code, body=data)
        return data

    def patch(self, ressource, payload, expected_code=204):
        code, data = self._cli.send_request(payload, path=ressource, method='PATCH')
        if code != expected_code:
            self.module.fail_json(msg=f"PATCH failed for '{ressource}'", status_code=code, body=data)
        return data

    def put(self, ressource, payload, expected_code=204):
        code, data = self._cli.send_request(payload, path=ressource, method='PUT')
        if code != expected_code:
            self.module.fail_json(msg=f"PUT failed for '{ressource}'", status_code=code, body=data)
        return data

    def post(self, ressource, payload, expected_code=201):
        code, data = self._cli.send_request(payload, path=ressource, method='POST')
        if code != expected_code:
            self.module.fail_json(msg=f"POST failed for '{ressource}'", status_code=code, body=data)
        return data

    def delete(self, ressource, expected_code=204):
        code, data = self._cli.send_request(None, path=ressource, method='DELETE')
        if code != expected_code:
            self.module.fail_json(msg=f"DELETE failed for '{ressource}'", status_code=code, body=data)
        return data

    def retrive_list(self, ressource):
        index = 0
        while True:
            if '?' in ressource:
                path = f"{ressource}&index={index}"
            else:
                path = f"{ressource}?index={index}"
            page = self.get(path)
            for item in page['list']:
                yield item
            if not page['hasMore']:
                return
            index += len(page['list'])

    def retrive_by_name(self, ressource, name, required=False, **kwargs):
        for item in self.retrive_list(ressource, **kwargs):
            if item['name'] == name:
                return self.get(f"{ressource.split('?')[0]}/{item['id']}")
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

    def retrive_users_by_name(self, name, required=False):
        query = dict(
            fullTextSearch=dict(
                type="OR",
                value=name,
                fields=["userName"]
            )
        )
        users = self.post('users/query', payload=query, expected_code=200)

        for user in users['list']:
            if user['userName'] == name:
                return user
        if required:
            self.module.fail_json(msg=f"Could not find user '{name}'.")
        return None

    @property
    def domainId(self):
        session = self.get('session')
        return session['domainId']
