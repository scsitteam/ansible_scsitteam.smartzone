# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Supercomputing Systems AG
# Copyright: (c) 2024, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    # Parameters for VMware modules
    DOCUMENTATION = r'''
options:
    location:
        description: String to describe the location
        type: str
    location_additional:
        description: String twith additional information to describe the location
        type: str
    latitude:
        description: Latitude coordinate (in decimal format)
        type: float
    longitude:
        description: Longitude coordinate (in decimal format)
        type: float
    altitude:
        description: Altitude information
        type: dict
        suboptions:
            unit:
                description: Unit of the altitude value.
                type: str
                default: meters
                choices: [meters, floor]
            value:
                description: Altitude
                type: int
'''
