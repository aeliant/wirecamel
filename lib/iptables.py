# coding=utf-8
import subprocess

from string import Template

SSLSPLIT_CONF = 'conf/iptables-configuration'
TMP_RULES = '/tmp/wirecamel-iptables-to-restore'


# Write the iptables configuration file
def write_conf(int1, int2, iptables_conf):
    # Known parameters
    parameters = {
        'int1': int1,
        'int2': int2,
        'HTTP_PORT': '80',
        'HTTP_JPORT': '8080',
        'HTTPS_PORT': '443',
        'HTTPS_JPORT': '8443'
    }

    # Configuration template string
    conf = Template("""*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [2:120]
:POSTROUTING ACCEPT [2:120]
-A PREROUTING -p tcp -m tcp --dport $HTTP_PORT -j REDIRECT --to-ports $HTTP_JPORT
-A PREROUTING -p tcp -m tcp --dport $HTTPS_PORT -j REDIRECT --to-ports $HTTPS_JPORT
-A POSTROUTING -o $int2 -j MASQUERADE
COMMIT

*filter
:INPUT ACCEPT [19:2455]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [25:2871]
-A INPUT -p tcp -m state --state NEW -m tcp --dport $HTTP_JPORT -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport $HTTPS_JPORT -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport $HTTPS_PORT -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport $HTTP_PORT -j ACCEPT
-A FORWARD -i $int1 -o $int2 -j ACCEPT
COMMIT
""").safe_substitute(parameters)

    # Writing conf
    with open(iptables_conf, 'w') as fconf:
        fconf.write(conf)


# Save actual set of rules
def save_rules():
    # Retrieving rules
    actual_rules = subprocess.check_output(['iptables-save'], shell=True)

    # Writing rules to a tmp file
    with open(TMP_RULES, 'w') as f:
        f.write(actual_rules)


# Restore iptables rules
def restore(rules_file):
    return subprocess.call("iptables-restore {}".format(rules_file), shell=True, stdout=subprocess.PIPE)


# Flush NAT rules
def flush_nat():
    return subprocess.call("iptables -t nat -F".split(" "), stdout=subprocess.PIPE)
