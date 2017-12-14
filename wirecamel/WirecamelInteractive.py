#!/usr/bin/env python
# coding=utf-8
import cmd
import codecs
import json
import pprint
import re
import subprocess
from dateutil import tz
from os import listdir, system
from os.path import isfile, join, getmtime

from tabulate import tabulate

from lib import style, sslsplit, util, core, hostapd, iptables, net


class WirecamelInteractive(cmd.Cmd):
    intro = """

     _    _ _          _____                      _                   ,,__
    | |  | (_)        /  __ \                    | |        ..  ..   / o._)                   .---.
    | |  | |_ _ __ ___| /  \/ __ _ _ __ ___   ___| |       /--'/--\\  \-'||        .----.    .'     '.
    | |/\| | | '__/ _ \ |    / _` | '_ ` _ \ / _ \ |      /        \\_/ / |      .'      '..'         '-.
    \  /\  / | | |  __/ \__/\ (_| | | | | | |  __/ |    .'\\  \\__\\  __.'.'     .'          -._
     \/  \/|_|_|  \___|\____/\__,_|_| |_| |_|\___|_|      )\ |  )\ |      _.'
                                                         // \\ // \\
                                                        ||_  \\|_  \\_
        [  Author  => Querdos  ]                        '--' '--'' '--'
        [  Version => 1.0      ]

    """

    # Initial configuration
    prompt = "wirecamel> "          # Prompt

    # Hostapd default param
    hostapd_options = {
        'interface': '',            # Interface for hostapd
        'driver': '',               # Driver to use for the access point
        'ssid': '',                 # SSID for the access point
        'channel': '',              # Channel of the access point
        'macaddr_acl': '',          # MAC address filter ?
        'hw_mode': '',              # Hardware mode (a = IEEE 802.11a, b = IEEE 802.11b, g = IEEE 802.11g)
        'auth_algs': '',            # Open Wifi or not
        'wpa': '',                  # Use of wpa ?
        'wpa_key_mgmt': '',         # Key mangement for the algorithm to use
        'wpa_passphrase': '',       # Passphrase for the access point
        'wpa_pairwise': '',         # WPA's data encryption
        'logger_syslog': '',        # Enable syslog for log management?
        'logger_syslog_level': '',  # Syslog level
        'logger_stdout': '',        # Enable stdout for log management ?
        'logger_stdout_level': ''   # Stdout log level
    }

    # Attributes
    filters = {
        'source_ip': '',            # Source IP to filter
        'source_port': '',          # Source port to filter
        'dest_ip': '',              # Destination IP to filter
        'dest_port': '',            # Destination port to filter
        'host': ''                  # Host to filter
    }

    # Main configuration variables
    # TODO: Change interfaces name for differenciation
    config = {
        'interface': '',
        'int_ap': '',               # Interface for the access point
        'bridge': '',               # Interface that will be used as a bridge to the internet
        'max_result': None,         # Max result to print
        'range_result': []          # Range result to print (5th to 10th for example)
    }

    files_association = {}
    headers = {}

    subhostapd = None               # Used to stop hostapd subprocess
    subssl = None                   # Used to stop sslsplit subprocess

    net_man_started = False         # Used to know if NetworkManager was started before launching SSLSplit

    # Initial configuration
    def preloop(self):
        # Checking if NetworkManager is running
        self.net_man_started = net.check_net_manager()

        # Checking if dependencies are installed
        util.check_dependencies()

        # Creating SSL Split directory structure if needed
        sslsplit.create_structure()

        # Generate certificates if needed
        sslsplit.generate_certs()

        # Reading hostapd configuration file
        self.hostapd_options = hostapd.load_config()

        # Clearing terminal
        system("clear")

    # Allow the user to configure interfaces (access point and internet access)
    def do_init_interfaces(self, value):
        """
        Allow the user to configure interfaces, i.e. which one will be used for spawning the access point and which
        will be used for the bridge.
        """
        # Retrieving interfaces (wireless and wired)
        wireless_interfaces = util.get_wireless_interface()
        net_interfaces = util.get_network_interfaces()

        # If only one interface, selecting it for the access point
        if len(wireless_interfaces) == 1:
            # Setting the interface for AP in conf
            # TODO: Remove
            self.config['interface'] = wireless_interfaces[0]

            self.config['int_ap'] = wireless_interfaces[0]
            self.config['bridge'] = 'lo'
        else:
            # Printing available interfaces
            print
            for wi in wireless_interfaces:
                active = '(active)' if net.is_active(wi) else '(not active)'
                print("[{}] {} {}".format(wireless_interfaces.index(wi), wi, active))

            print
            user_choice = -1

            # Asking to select a wireless interface for the access point
            while user_choice < 0 or user_choice >= len(wireless_interfaces):
                user_choice = raw_input("Select a wireless interface for the access point: ")
                try:
                    user_choice = int(user_choice)
                    self.config['interface'] = wireless_interfaces[user_choice]
                    self.hostapd_options['interface'] = wireless_interfaces[user_choice]
                except ValueError:
                    user_choice = -1
                    continue

            # Write iptables and hostapd configuration
            iptables.write_conf(wireless_interfaces[user_choice], net_interfaces[0], iptables.SSLSPLIT_CONF)
            hostapd.save_config(self.hostapd_options)

    # Print initial configuration and allow the user to edit it
    def do_init_config(self, value):
        """init_config
        Print initial configuration parameters and their values or change it by
        specifying which one and with which value
        """
        # If no arguments specified, just printing initial config
        if not value:
            table_print = []
            for conf_key in self.config:
                if None is not self.config[conf_key]:
                    table_print.append([conf_key, self.config[conf_key]])
                else:
                    table_print.append([conf_key, 'Not set'])

            print(tabulate(table_print, tablefmt="fancy_grid"))
        else:
            arguments = value.split(" ")
            if len(arguments) != 1:
                if arguments[0] in self.config:
                    # Specific handling for range result
                    if arguments[0] == 'range_result':
                        if len(arguments) == 3:
                            try:
                                if 0 <= int(arguments[1]) < int(arguments[2]):
                                    self.config[arguments[0]] = [int(arguments[1]), int(arguments[2])]
                                else:
                                    style.fail("Usage: init_config range_result a b (0 <= a < b)")
                            except ValueError:
                                style.fail("Values must be integer")
                        else:
                            style.fail("Usage: init_config range_result min_value max_value")

                    # Specific handling for uri
                    elif arguments[0] == 'save_dir':
                        if value.startswith("save_dir '"):
                            sslsplit.SAVE_DIR = util.purify_uri(value[len("save_dir '"):-1])
                        elif value.startswith("save_dir \""):
                            sslsplit.SAVE_DIR = util.purify_uri(value[len("save_dir \""):-1])
                        else:
                            sslsplit.SAVE_DIR = util.purify_uri(arguments[1])
                    else:
                        # Setting value for the given parameter
                        self.config[arguments[0]] = arguments[1]
                else:
                    style.fail("Unknown parameter.")
            else:
                style.fail("Usage: init_config | init_config param value")

    # Completion for init_config
    def complete_init_config(self, text, line, begidx, endidx):
        return [i for i in self.config if i.startswith(text)]

    # Print filters and allow the user to edit it
    def do_filters(self, value):
        if not value:
            table_print = []
            for fil in self.filters:
                if len(self.filters[fil]) == 0:
                    table_print.append([fil, 'Not set'])
                else:
                    table_print.append([fil, self.filters[fil]])

            print(tabulate(table_print, tablefmt="fancy_grid"))
        else:
            arguments = value.split(" ")
            if len(arguments) == 2:
                if arguments[0] in self.filters:
                    self.filters[arguments[0]] = arguments[1]
                else:
                    style.fail("Unknown filter")
            else:
                style.fail("Usage: filters | filters filter_name filter_value")

    # Completion for fitlers
    def complete_filters(self, text, line, begidx, endidx):
        return [i for i in self.filters if i.startswith(text)]

    # Print Acess Point (Hostapd) configuration
    def do_ap_config(self, value):
        """ap_config
        Print the access point configuration and allow the user to change default values
        """
        if not value:
            table_print = []
            for key in self.hostapd_options:
                table_print.append([key, self.hostapd_options[key]])

            print("\n=================================")
            print("\tHostapd configuration")
            print("=================================")
            print(tabulate(table_print, tablefmt='fancy_grid'))
        else:
            arguments = value.split(" ")
            if len(arguments) == 2:
                if arguments[0] in self.hostapd_options:
                    self.hostapd_options[arguments[0]] = arguments[1]
                    hostapd.save_config(self.hostapd_options)
                else:
                    style.fail("Usage: ap_config | ap_config config_param value")
            else:
                style.fail("Usage: ap_config | ap_config config_param value")

    # Start SSLSplit
    def do_start_sslsplit(self, line):
        """start_sslsplit
        Start SSL Split as an access point
        """
        # Checking if sslsplit already started
        if not isinstance(self.subssl, subprocess.Popen):
            # Starting SSL Split
            (self.subhostapd, self.subssl) = sslsplit.start(self.config['interface'])
        else:
            style.fail("Please setup interface for the access point")

    # Stop SSL Split and clean
    def do_stop_sslsplit(self, line):
        """stop_sslsplit
        Stop the access point and SSL Split
        """
        if self.subssl is None:
            style.fail("SSL Split and hostapd not started")
        else:
            # Stopping
            sslsplit.stop(
                self.subssl,
                self.subhostapd,
                self.net_man_started
            )

            # Resetting processes
            self.subssl = None
            self.subhostapd = None

    # Reset Filters
    def do_reset_filters(self, line):
        """reset_filters
        Reset filters (Source IP, Source Port, etc.)
        """
        for key in self.filters.keys():
            self.filters[key] = ''

    # Log file parsing
    def do_parse(self, value):
        """parse [logfile_id]
        Parse the given log file id.
        You must run show_connection first in order to retrieve all files in sslsplit logs directory
        """
        if value:
            if len(self.files_association) == 0:
                style.fail("The list is empty. Please first use show_connections to parse existing files.")
            elif value in self.files_association:
                # Retrieving log filename
                log_filename = self.files_association[str(value)]

                # Opening the file
                with open(sslsplit.LOGS_DIR + log_filename) as log_file:
                    m = re.match(r'(.*)-(.*),(.*)-(.*),(.*)\.log', log_filename)
                    if m:
                        # Parsing the request
                        self.headers = core.parse_logfile(log_file)
                    else:
                        # Error
                        print("Incorrect file format.\n")
            else:
                style.fail("This id is not in the list. Please launch show_connections for a list of id")

        else:
            style.fail("Usage: parse log_id (can be retrieved after showing connections)")

    # Allow the user to save responses, requests or stream
    def do_save(self, value):
        """save [requests|responses|stream]
        Save to a save directory either all responses, requests or the entire stream
        """
        # Handling saving all
        if len(value.split(" ")) == 1 and value.split(" ")[0] == 'all':
            for filename in self.files_association:
                with open("{}{}".format(sslsplit.LOGS_DIR, filename)) as file_object:
                    # TODO
                    headers = core.parse_logfile(file_object)

        # Handling requests, responses and stream saving all
        elif len(self.headers) != 0:
            if value:
                # Checking arguments
                arguments = value.split(" ")
                if len(arguments) == 1 and arguments[0] in ['requests', 'responses', 'stream']:
                    # Asking for filename
                    filename = ""
                    while len(filename) == 0:
                        filename = raw_input("Filename: ")
                        if len(filename) != 0 and isfile("{}{}".format(sslsplit.SAVE_DIR, filename)):
                            style.fail(
                                "{}{} already exists, please choose a new filename".format(
                                    self.config['save_dir'], filename
                                )
                            )
                            filename = ""

                    # Opening the file for write operation
                    save_file = codecs.open("{}{}".format(sslsplit.SAVE_DIR, filename), 'w', encoding='utf-8')

                    # Checking what the user want to save
                    table_tosave = []
                    if arguments[0] == 'stream':
                        save_file.write(core.printable_headers(self.headers))
                    else:
                        save_file.write(core.printable_headers(self.headers[arguments[0]]))

                    # Closing the file
                    style.print_call_info(0, "", "Saved successfuly ({}{})".format(sslsplit.SAVE_DIR, filename))
                    save_file.close()
                else:
                    style.fail("Usage: save [requests|responses|stream]")
            else:
                style.fail("Usage: save [requests|responses|stream]")
        else:
            style.fail("No log selected, please run show_connections and parse first")

    # Completion for save command
    def complete_save(self, text, line, begidx, endidx):
        return [i for i in ['requests', 'responses', 'stream', 'all'] if i.startswith(text)]

    # TODO: save all streams
    def save_all_streams(self, headers):
        pprint.pprint(headers)
        print("TODO")

    # Allow the user to print responses, requests or the entire stream
    def do_print(self, value):
        """print [requests|responses|stream|filename]
        Print either all responses, requests or the entire stream
        """
        arguments = value.split(" ")

        # Handling filename printing
        if len(arguments) == 2 and arguments[0] == 'filename':
            if arguments[1] in self.files_association:
                print(self.files_association[str(arguments[1])])
            else:
                style.fail(
                    "No id found in association array. Please use show_connection for more "
                    "information")

        elif len(self.headers) != 0:
            if value:
                # Checking arguments
                arguments = value.split(" ")
                if 1 == len(arguments) and arguments[0] in ['requests', 'responses', 'stream']:
                    # Checking what the user wants to print
                    if arguments[0] == 'stream':
                        print(core.printable_headers(self.headers))
                    else:
                        print(core.printable_headers(self.headers[arguments[0]]))
                else:
                    style.fail("Usage: print [requests|responses|stream]")
            else:
                style.fail("Usage: print [requests|response|stream]")
        else:
            style.fail("You need to parse a file first. Please refer to show_connections and parse.")

    # Completion for print command
    def complete_print(self, text, line, begidx, endidx):
        return [i for i in ['requests', 'responses', 'stream', 'filename'] if i.startswith(text)]

    # Print statistics for current session
    def do_stats(self, line):
        """
        Print statistics for current sessions (Total POST, GET, PUT, etc.)
        """
        if len(self.files_association) != 0:
            stats_table = {}
            for log in self.files_association.values():
                m = re.match(r'(.*)-(.*),(.*)-(.*),(.*)\.log', log)

                # Retrieving number of requests (POST, HEAD, GET, whatever)
                with open(sslsplit.LOGS_DIR) as log_file:
                    content_total = 0
                    total_post = 0
                    total_get = 0
                    total_put = 0
                    total_head = 0

                    try:
                        result = core.parse_logfile(log_file)

                        requests = len(result['requests'])

                        for request in result['requests']:
                            if 'Content-Length' in request:
                                content_total += int(request['Content-Length'])

                            # Methods stats
                            if 'POST' == request['Method']:
                                total_post += 1
                            if 'GET' == request['Method']:
                                total_get += 1
                            if 'PUT' == request['Method']:
                                total_put += 1
                            if 'HEAD' == request['Method']:
                                total_head += 1
                    # TODO: problem with chunked data
                    except ValueError:
                        continue

                # Adding source ip if not present
                if m.group(2) not in stats_table:
                    stats_table[m.group(2)] = {}

                # Checking if destination ip is present
                if m.group(4) not in stats_table[m.group(2)]:
                    stats_table[m.group(2)][m.group(4)] = {
                        'count': requests,
                        'content-total': content_total,
                        'get-total': total_get,
                        'post-total': total_post,
                        'put-total': total_put,
                        'head-total': total_head
                    }
                else:
                    stats_table[m.group(2)][m.group(4)]['count'] += requests
                    stats_table[m.group(2)][m.group(4)]['content-total'] += content_total
                    stats_table[m.group(2)][m.group(4)]['get-total'] += total_get
                    stats_table[m.group(2)][m.group(4)]['post-total'] += total_post
                    stats_table[m.group(2)][m.group(4)]['put-total'] += total_put
                    stats_table[m.group(2)][m.group(4)]['head-total'] += total_head

            # Filling printing table
            table_print = {}
            headers = [
                'Destination IP',
                'Requests',
                'Total Content-Length sent',
                'Total POST',
                'Total GET',
                'Total PUT',
                'Total HEAD'
            ]
            for ipsrc in stats_table:
                if ipsrc not in table_print:
                    table_print[ipsrc] = []

                for ipdst in stats_table[ipsrc]:
                    table_print[ipsrc].append(
                        [
                            ipdst,
                            stats_table[ipsrc][ipdst]['count'],
                            stats_table[ipsrc][ipdst]['content-total'],
                            stats_table[ipsrc][ipdst]['post-total'],
                            stats_table[ipsrc][ipdst]['get-total'],
                            stats_table[ipsrc][ipdst]['put-total'],
                            stats_table[ipsrc][ipdst]['head-total']
                        ]
                    )

            for ipsrc in table_print:
                print("============================")
                print("\t{}".format(ipsrc))
                print("============================")
                print(tabulate(table_print[ipsrc], headers=headers, tablefmt='fancy_grid'))
                print

        else:
            style.fail("Please run `show_connections` first in order to print statistics.")

    # Show connections made since SSL Split is launched
    def do_show_connections(self, line):
        """show_connections
        Show connections made since SSL Split is launched
        """
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Paris')  # TODO: Timezone ?

        # Reseting (if needed) headers
        self.headers = {}
        self.files_association = {}

        # Listing all files in dir
        files = [
            f for f in listdir(sslsplit.LOGS_DIR)
            if isfile(join(sslsplit.LOGS_DIR, f))
        ]
        files.sort(key=lambda x: getmtime(sslsplit.LOGS_DIR + x))

        # Printing informations for each file
        table = []
        headers = ['Id', 'Creation date', 'Source IP', 'Source Port', 'Destination IP', 'Destion Port',
                   'Host', 'Id']

        file_id = 1
        for log_file in files:
            # Checking range
            if len(self.config['range_result']) != 0:
                if file_id not in range(self.config['range_result'][0], self.config['range_result'][1]+1):
                    file_id += 1
                    continue

                # No need to continue if id is greater than the range
                if file_id > self.config['range_result'][1]:
                    break

            # Parsing filename
            file_info = core.parse_logfilename(log_file)

            if len(self.filters['source_ip']) != 0 and self.filters['source_ip'] != file_info['source_ip']:
                continue
            if len(self.filters['source_port']) != 0 and self.filters['source_port'] != file_info['source_port']:
                continue
            if len(self.filters['dest_ip']) != 0 and self.filters['dest_ip'] != file_info['destination_ip']:
                continue
            if len(self.filters['dest_port']) != 0 and self.filters['dest_port'] != file_info['destination_port']:
                continue

            # Parsing file
            with open(sslsplit.LOGS_DIR + log_file, 'r') as f:
                # f = open(self.sslsplit_log_dir+file, 'r')
                host = "-"
                for line in f.readlines():
                    mhost = re.findall(r'Host: (.*)\r', line)
                    if len(mhost) != 0:
                        host = mhost[0]
                        break

            if len(self.filters['host']) != 0 and self.filters['host'] != host:
                continue

            # Appending data
            table.append([
                file_id,
                file_info['date'],
                file_info['source_ip'],
                file_info['source_port'],
                file_info['destination_ip'],
                file_info['destination_port'],
                host,
                file_id
            ])
            self.files_association[str(file_id)] = log_file

            # Checking for max result to print
            if self.config['max_result'] is not None and file_id == int(self.config['max_result']):
                break

            file_id += 1

        print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

    # Show information for the given log id (internet protocol, whois)
    def do_show_information(self, value):
        """show_information [log_id]
        Print IP information and whois informations
        """
        if value:
            if len(self.files_association) == 0:
                style.fail(
                    "The list is empty. Please first use show_connections to parse existant files."
                )
            # Checking if value is a correct id
            elif value in self.files_association:
                # Retrieving filename
                log_filename = self.files_association[str(value)]
                m = re.match(r'(.*)-(.*),(.*)-(.*),(.*)\.log', log_filename)

                # Internet Protocol information
                table_ip = [
                    ['Source IP', m.group(2)],
                    ['Source Port', m.group(3)],
                    ['Dest IP', m.group(4)],
                    ['Dest Port', m.group(5)]
                ]

                # Whois informations
                info = util.whois_information(m.group(4))
                table_whois = [
                    ['NetName', info['netname']],
                    ['Organization', info['organization']],
                    ['City', info['city']],
                    ['Country', info['country']]
                ]

                # Printing informations
                print("\n====================================================")
                print("\tInternet Protocol informations")
                print("====================================================")
                print(tabulate(table_ip, tablefmt='fancy_grid'))
                print
                print("====================================================")
                print("\tWhois informations")
                print("====================================================")
                print(tabulate(table_whois, tablefmt='fancy_grid'))
                print
                util.whois_information(m.group(4))
            else:
                style.fail("This id is not a valid one. Please use show_connections for more informations")
        else:
            style.fail("Usage: show_information [log_id]")

    # Do a backup of log files and the connections log file
    def do_backup_and_clean(self, line):
        """backup_and_clean
        Make a backup of all log files in sslsplit-logs directory (saving in the save_dir directory)
        """
        filename = ""
        while len(filename) == 0:
            filename = raw_input("Name for the backup (without extension)? ")

        # Saving
        sslsplit.save_logs(filename)

        style.print_call_info(0, "tar", "Saved backup and cleaned directory".format(sslsplit.SAVE_DIR))

    # Base 64 decoding function
    @staticmethod
    def do_base64_decode(value):
        """base64_decode
        Decode a string, base64 encoded
        """
        newvalue = value.decode("base64")
        print(newvalue)

    # Prettify JSON formatted text
    @staticmethod
    def do_pretty_simplejson(value):
        """pretty_simplejson
        Prettify JSON (simple) input
        """
        table = []
        json_data = json.loads(value)
        for key in json_data.keys():
            table.append([key, json_data[key]])

        print(tabulate(table, tablefmt="fancy_grid"))

    # Prettify URI
    def do_pretty_uri(self, value):
        if value:
            print(value.replace("&", "\n").replace("=", " = "))
        else:
            style.fail("Usage: pretty_uri [uri]")

    def emptyline(self):
        pass

    # Exit the program
    def do_bye(self, line):
        """bye
        Exit the program"""
        exit(0)

    def do_EOF(self, line):
        """do_EOF
        End Of File function
        """
        return True
