# coding=utf-8
import re


# Load hostapd configuration
def load_hostapd_conf(conf_file):
    hostapd_options = {}

    with open(conf_file, 'r') as hap_file:
        for line in hap_file.readlines():
            elements = re.findall(r'(.*)=(.*)\n', line)
            if len(elements) != 0:
                hostapd_options[elements[0][0]] = elements[0][1]

    return hostapd_options


# Save hostapd configuration
def save_config(config, path_conf_file):
    with open(path_conf_file, 'w') as f:
        for key in config:
            f.write("{}={}\n".format(key, config[key]))
