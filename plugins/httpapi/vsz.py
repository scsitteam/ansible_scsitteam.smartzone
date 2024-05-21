# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
author:
    - Marius Rieder (@jiuka)
name: vsz
short_description: Use Ruckus SmartZone RestAPI
description:
  - This HttpApi plugin provides methods to connect to Ruckus SmartZone Public API over a HTTP(S).
'''

import json

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.six.moves.urllib.error import HTTPError

BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}


class HttpApi(HttpApiBase):
    def login(self, username, password):
        self.connection._auth = {}
        if username and password:
            payload = dict(
                username=username,
                password=password,
            )
        else:
            raise AnsibleConnectionFailure('Username and password are required for login')

        # Login
        code, data = self.send_request(payload, path='serviceTicket', method='POST')
        if code != 200:
            if 'message' in data:
                raise AnsibleConnectionFailure(data['message'])
            raise AnsibleConnectionFailure('[%s] %s'.format(code, data))
        self.connection._service_ticket = data['serviceTicket']

    def logout(self):
        self.send_request(None, path='serviceTicket', method='DELETE')

    @property
    def api_info(self):
        if not hasattr(self.connection, '_api_info'):
            resp, response_data = self.connection.send(
                '/wsg/api/public/apiInfo',
                None,
                method='GET',
                headers=BASE_HEADERS,
            )
            data = to_text(response_data.getvalue())
            if data:
                data = json.loads(data)

            if resp.getcode() != 200 or 'apiSupportVersions' not in data:
                raise AnsibleConnectionFailure('Could not connect to endpoint %s/wsg/api/public/apiInfo'.format(self.connection._url))

            setattr(self.connection, '_api_info', data)
        return getattr(self.connection, '_api_info')

    @property
    def latest_version(self):
        return self.api_info['apiSupportVersions'][-1]

    def send_request(self, data, path, method='POST'):
        path = '/wsg/api/public/%s/%s'.format(self.latest_version, path)
        self._display_request(method, path)
        if hasattr(self.connection, '_service_ticket'):
            path = '%s?serviceTicket=%s'.format(path, self.connection._service_ticket)

        if data:
            data = json.dumps(data)

        try:
            response, response_data = self.connection.send(
                path,
                data,
                method=method,
                headers=BASE_HEADERS,
            )
            response_value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(response_value)
        except AnsibleConnectionFailure:
            return 404, 'Object not found'
        except HTTPError as e:
            return e.code, json.loads(e.read())

    def _display_request(self, method, path):
        self.connection.queue_message(
            "vvvv",
            'Web Services: %s %s%s'.format(method, self.connection._url, path)
        )

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        except json.JSONDecodeError:
            raise ConnectionError('Invalid JSON response: %s'.format(response_text))
