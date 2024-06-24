# -*- coding: utf-8 -*-

# Copyright (c) 2024, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ApBasicConfig:
    def __init__(self, options):
        self.options = self.to_dict(options)

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
        return  [
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

    def update(self, update, current={}):
        for key in self.options:
            if current.get(key) != self.options[key]:
                update[key] = self.options[key]
