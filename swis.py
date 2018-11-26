# (c) 2015, Brian Coca <bcoca@ansible.com>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Use SolarWinds SWIS client api to access(r/w) Orion DB from within a playbook

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: swis
author: anon
version_added: yes
short_description: return contents from OrionSDK
description:
    - Returns the value of a column from the nodes view.
options:
  _terms:
    description: list of hostnames to query for column
  npm_server:
    IP of Orion server
  column:
    description: value from nodes view to be returned
    type: string
    default: nodes.customproperties.serialNumber
  user_id:
    description: userID to connect to OrionSDK with
    type: string
    default: **
  passwd:
    description: password to connect to OrionSDK with
    type: string
    default: **
  update_flag:
    description: update the value in Orion
    type: boolean
    default: False
  new_value:
    description: update the value in Orion
    type: string
    default: ''
  
"""

EXAMPLES = """
- name: url lookup splits lines by default
  debug: msg="{{item}}"
  loop: "{{ lookup('url', 'https://github.com/gremlin.keys', wantlist=True) }}"

- name: display ip ranges
  debug: msg="{{ lookup('url', 'https://ip-ranges.amazonaws.com/ip-ranges.json', split_lines=False) }}"
"""

RETURN = """
  _list:
    the column from orion API
"""
import requests
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from orionsdk import SwisClient
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        npm_server = kwargs.get('npm_server', '172.19.128.111')
        column = kwargs.get('column', 'nodes.customproperties.serialNumber')
        user_id = kwargs.get('user_id', '**')
        passwd = kwargs.get('passwd', '**')
        update_flag = kwargs.get('update_flag', False)
        new_value = kwargs.get('new_value', '')

        
        # lookups in general are expected to both take a list as input terms[], and output a list, ret[]
        # this is done so they work with the looping construct 'with_'.
        ret = []

        for hostname in terms:
            display.v("value to return %s" % column)
            query = "SELECT {} FROM Orion.Nodes WHERE Caption = '{}'".format(column, hostname)
            
            display.v("query: {}".format(query))

            try:
                orion = self.orion_connect(npm_server, user_id, passwd)
                rsp = self.orion_query(orion, query)
                display.v("result: {}".format(rsp['results'][0][rsp['results'][0].keys()[0]]))
                if update_flag:
                    display.v("update {} with {}".format(column, new_value))
                    uri_query = "SELECT URI from Orion.Nodes WHERE Caption = '{}'".format(hostname)
                    uri = self.orion_query(orion, uri_query)
                    url = "{}/{}".format(uri['results'][0]['URI'], column.split('.')[-2])
                    display.v("url: {}".format(url))
                    orion.update(url, **{ column.split('.')[-1] : new_value } )

            except HTTPError as e:
                raise AnsibleError("Received HTTP error for %s : %s" % (hostname, str(e)))
            except URLError as e:
                raise AnsibleError("Failed lookup url for %s : %s" % (hostname, str(e)))
            except SSLValidationError as e:
                raise AnsibleError("Error validating the server's certificate for %s: %s" % (hostname, str(e)))
            except ConnectionError as e:
                raise AnsibleError("Error connecting to %s: %s" % (hostname, str(e)))
            except Exception as e:
                raise AnsibleError("Error:  %s: %s" % (hostname, str(e)))
            else:
                display.v("response {}".format(rsp['results'][0].keys()[0]))
                ret.append(to_text(rsp['results'][0][rsp['results'][0].keys()[0]]))
        return ret

    def orion_connect(self, npm_server, username, password):
        """ Open connection to Orion server """
        requests.packages.urllib3.disable_warnings()
        swis = SwisClient(npm_server, username, password)
        return swis

    def orion_query(self, swis, query):
        """ Connect to Orion server and send query """
        rsp = swis.query("{}".format(query))
        if rsp['results'] == []:
            print("No results for: {}".format(query))
            exit(-1)
        display.v("Query Orion Existing SerialNumber: {}\n".format(rsp['results'][0][rsp['results'][0].keys()[0]]))
        return rsp


