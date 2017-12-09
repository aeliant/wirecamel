# coding=utf-8
import re
import subprocess

import style

# List of required dependencies
DEPS = [
    'hostapd',
    'sslsplit',
    'dhcpd',
    'xterm',
    'dnsmasq',
    'aircrack-ng',
    'iwconfig',
    'whois'
]


# Checking Linux distribution
def check_distro():
    p = subprocess.Popen(
        "lsb_release -a",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = re.search("Distributor ID:\s+([a-zA-Z]+)", p.stdout.read())

    return {
        'debian': 'Debian' == res.group(1),
        'ubuntu': 'Ubuntu' == res.group(1),
        'mageia': 'Mageia' == res.group(1)
    }


# Check dependencies and ask to install if needed
def check_dependencies():
    not_installed = []
    user_choice = ['y', 'Y', 'n', 'N']

    # For each dep, checking installed
    for dep in DEPS:
        p = subprocess.Popen(
            "which {}".format(dep),
            shell=True,
            stdout=subprocess.PIPE
        )

        # Appending missing packages
        if len(p.stdout.read()) == 0:
            not_installed.append(dep)

    # Printing info and asking to install if needed
    if len(not_installed) != 0:
        # Printing missing packages
        print("The following packages are missing:")
        for pack in not_installed:
            print("\t * {}".format(pack))

        # Asking to install
        choice = 'a'
        while (choice not in user_choice) and len(choice) >= 1:
            choice = raw_input("Do you want to install them ? [Y/n]")

        # Returning false if deps are not installed
        if choice in ['n', 'N']:
            style.fail('Aborting.')
            return
        else:
            # Debian & Ubuntu based
            if check_distro()['debian'] or check_distro()['ubuntu']:
                # Base command
                cmd = "apt-get install -y".split(" ")

                # Adding missing packages to the installation list
                for pckg in not_installed:
                    if pckg == 'iwconfig':
                        cmd.append('net-tools')
                    else:
                        cmd.append(pckg)

                # Executing command and waiting the completion
                p = subprocess.Popen(cmd)
                p.wait()

                return
            else:
                print("Not yet implemented. Please install packages manually.")
                style.fail('Aborting.')
                return
    else:
        return


# Return wireless interfaces
def get_wireless_interface():
    data = subprocess.check_output(
        "iwconfig",
        shell=True,
        stderr=subprocess.PIPE
    )
    return re.findall(r'([a-zA-Z0-9]+)\s+IEEE', data)


# Return all network interfaces (except loopback)
def get_network_interfaces():
    data = subprocess.check_output(
        "ls /sys/class/net | grep -v ^lo",
        shell=True,
        stderr=subprocess.PIPE
    )

    return data.strip().split('\n')


# Whois informations
def whois_information(ip):
    # Executing whois command
    result = subprocess.check_output(['whois', ip])

    # Retrieving information
    info = {
        'netname': re.findall(r'NetName:\s+(.*)\n', result),
        'organization': re.findall(r'Organization:\s+(.*)\n', result),
        'city': re.findall(r'City:\s+(.*)\n', result),
        'country': re.findall(r'Country:\s+(.*)\n', result)
    }

    # Reorganizing data
    for key in info:
        info[key] = info[key][0] if len(info[key]) != 0 else ''

    # Returning data
    return info


# Clean absolute URI
def purify_uri(uri):
    return uri if re.match(r'.*/$', uri) else uri + '/'
