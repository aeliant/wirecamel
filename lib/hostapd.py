# coding=utf-8
import re
import subprocess

CONF = 'conf/hostapd.conf'
XTERM_TITLE = 'Hostapd console'


# Load hostapd configuration
def load_config():
    hostapd_options = {}

    with open(CONF, 'r') as hap_file:
        for line in hap_file.readlines():
            elements = re.findall(r'(.*)=(.*)\n', line)
            if len(elements) != 0:
                hostapd_options[elements[0][0]] = elements[0][1]

    return hostapd_options


# Save hostapd configuration
def save_config(config):
    with open(CONF, 'w') as f:
        for key in config:
            f.write("{}={}\n".format(key, config[key]))


# Start hostapd
def start(xterm=True):
    if xterm:
        return subprocess.Popen(
            ['xterm', '-T', XTERM_TITLE, '-hold', '-e', 'hostapd', '-d', CONF]
        )
    else:
        return subprocess.Popen(
            ['hostapd', '-d', CONF]
        )
