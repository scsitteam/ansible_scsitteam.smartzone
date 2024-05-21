#!/usr/bin/python
#
# (c) 2024 Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

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