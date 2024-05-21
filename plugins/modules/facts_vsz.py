#!/usr/bin/python
#
# (c) 2024 Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: facts_vsz

short_description: Gathers facts the SmartZone instance

description:
    - This module can be used to gathers facts bouthe the SmartZone api and cluster.

author:
    - Marius Rieder (@jiuka)
'''

EXAMPLES = r'''
- name: Gather SmartZone facts
  scsitteam.smartzone.facts_vsz:
'''

RETURN = r'''
ansible_facts:
  description: info about the SmartZone instance
  returned: always
  type: dict
  sample:
    {
        "smartzone_admin_id": "01234567-89ab-cdef-0000-0123456789ab",
        "smartzone_api_latest_version": "v11_1",
        "smartzone_api_supported_version": [
            "v9_0",
            "v9_1",
            "v10_0",
            "v11_0",
            "v11_1"
        ],
        "smartzone_cluster_name": "ANSIBLE-TEST-CLUSTER",
        "smartzone_cluster_role": "Leader",
        "smartzone_cluster_state": "In_Service",
        "smartzone_domain_id": "01234567-89ab-cdef-0000-0123456789ab",
        "smartzone_node_id": "01234567-89ab-cdef-0000-0123456789ab",
        "smartzone_node_name": "smartzone"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scsitteam.smartzone.plugins.module_utils.vsz import SmartZoneConnection

def main():
    """main entry point for module execution
    """
    module = AnsibleModule(argument_spec=dict(),
                           supports_check_mode=True)
    conn = SmartZoneConnection(module)

    session = conn.get('session')
    cluster_state = conn.get('cluster/state')

    facts = dict(
        smartzone_api_supported_version=session['apiVersions'],
        smartzone_api_latest_version=session['apiVersions'][-1],
        smartzone_admin_id=session['adminId'],
        smartzone_domain_id=session['domainId'],
        smartzone_cluster_name=cluster_state['clusterName'],
        smartzone_cluster_state=cluster_state['clusterState'],
        smartzone_cluster_role=cluster_state['clusterRole'],
        smartzone_node_id=cluster_state['currentNodeId'],
        smartzone_node_name=cluster_state['currentNodeName'],
    )

    module.exit_json(ansible_facts=facts)


if __name__ == '__main__':
    main()