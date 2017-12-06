# coding=utf-8
import subprocess
import shutil
import re

from os.path import isfile
from os import unlink

WIRECAMEL_CONF = 'conf/dnsmasq.conf'
ACTUAL_CONF = '/etc/dnsmasq.conf'
TMP_CONF = '/tmp/wirecamel-dnsmasq.conf'

RANGE_IP_FIRST = '10.0.0.10'
RANGE_IP_LAST = '10.0.0.100'
ROUTER_IP = '10.0.0.1'


# Load configuration file
def load_conf():
    # Creating new array
    conf_array = {}

    # Reading configuration file
    with open(WIRECAMEL_CONF, 'r') as conf:
        # For each line
        for line in conf.readlines():
            # Find conf name and value
            match = re.search(r'(.*)=(.*)', line)
            conf_array[match.group(1)] = match.group(2)

    return conf_array


# Write new configuration file, with a given interface
def write_conf(interface):
    conf = """interface={}
cache-size=256
dhcp-range={},{},24h
dhcp-option=23,64
""".format(interface, RANGE_IP_FIRST, RANGE_IP_LAST)

    with open(WIRECAMEL_CONF, 'w') as f:
        f.write(conf)


# Start a new daemon of dnsmasq
def start():
    # Checking if configuration file exists
    if isfile(ACTUAL_CONF):
        # Save actual dnsmasq.conf
        shutil.copyfile(ACTUAL_CONF, TMP_CONF)

    # Copy wirecamel dnsmasq conf
    shutil.copyfile(WIRECAMEL_CONF, ACTUAL_CONF)

    # Starting the service
    return subprocess.call(['systemctl', 'start', 'dnsmasq'], stdout=subprocess.PIPE)


# Stop the dnsmasq daemon
def stop():
    # Stopping the service
    res = subprocess.call(['systemctl', 'stop', 'dnsmasq'], stdout=subprocess.PIPE)

    # Restoring old configuration
    shutil.copyfile(TMP_CONF, ACTUAL_CONF)

    # Removing tmp configuration
    unlink(TMP_CONF)

    # Returning subprocess result
    return res
