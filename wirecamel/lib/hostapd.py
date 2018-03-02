# coding=utf-8
from wirecamel import CONF_DIR

import re
import subprocess
import yaml

XTERM_TITLE = 'Hostapd console'

# Load hostapd configuration
def load_config():
    hostapd_options = {}

    with open(CONF_DIR, 'r') as hap_file:
        for line in hap_file.readlines():
            elements = re.findall(r'(.*)=(.*)\n', line)
            if len(elements) != 0:
                hostapd_options[elements[0][0]] = elements[0][1]

    return hostapd_options

# Save hostapd configuration
def save_config(config):
    yaml.dump(config,
              stream=open('{0}/hostapd.yaml'.format(CONF_DIR), 'w'),
              default_flow_style=False)

# Start hostapd
def start(xterm=True):
    if xterm:
        return subprocess.Popen(
            ['xterm', '-T', XTERM_TITLE, '-hold', '-e', 'hostapd', '-d', CONF_DIR]
        )
    else:
        return subprocess.Popen(
            ['hostapd', '-d', CONF_DIR]
        )
