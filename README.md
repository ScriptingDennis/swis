# swis
lookup_plugins/ swis : call from Ansible playbook to r/w columns from Orion DB not included as columns in dynamic inventory. uses SolarWinds swis api

Goes under playbook folder, e.g;
>Playbooks
>├── lookup_plugins
>│   ├── swis.py`

### Call it from within palybook to read a vlaue not included in the dynamic inventory script;
using default connection string values
`
  - name: Get Values From Orion -swis plugin default column value is SerialNumber
    set_fact: 
      serialno:    "{{ q('swis', inventory_hostname) }}"
`

### Call it from within playbook to update a value;
  using provided connection string values
`
  - name: Update serial number on Orion via SDK
    debug: 
      msg: "{{inventory_hostname}} was: {{item[0]}}, Changed to: {{ansible_net_serialnum}}"
    loop: "{{ q('swis', inventory_hostname, update_flag=true, new_value= ansible_net_serialnum, user_id=orion_user, passwd=orion_pass) }}"
    changed_when: "item[0] != ansible_net_serialnum"
`
