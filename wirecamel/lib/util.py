# coding=utf-8
from wirecamel import CONF_DIR

import yaml
import re
import subprocess
import style

def check_distro():
    """ Check which distribution the user run Wirecamel """
    # retrieving linux distribution
    from platform import linux_distribution
    distro = linux_distribution()[0]

    # returning value
    return distro if distro != '' else False

def check_dependencies(distrib):
    """ Check if required dependencies are installed and ask the user ot install them if needed """
    not_installed   = []
    user_choice     = ['y', 'Y', 'n', 'N']

    # loading required deps
    deps = yaml.safe_load(
        open('{0}/packages.yaml'.format(CONF_DIR), 'r')
    )['dependencies-{0}'.format(distrib)]

    # For each dep, checking installed
    for dep in deps:
        p = subprocess.Popen(
            "which {0}".format(dep),
            shell   = True,
            stdout  = subprocess.PIPE,
            stderr  = subprocess.PIPE
        )

        # Appending missing packages
        if len(p.stdout.read()) == 0:
            not_installed.append(dep)

    # Printing info and asking to install if needed
    if len(not_installed) != 0:
        # Printing missing packages
        print("The following packages are missing:")
        for pack in not_installed:
            print("\t * {0}".format(pack))

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
            if check_distro() == 'debian' or check_distro() == 'ubuntu':
                print('installing')
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
                if not check_distro():
                    print("Unrecognized linux distribution. Please install packages manually.")
                else:
                    print("Please install packages manually, since your distribution is not handled yet.")

                style.fail('Aborting.')
                exit(1)
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
