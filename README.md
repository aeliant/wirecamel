# Wirecamel

     _    _ _          _____                      _                   ,,__
    | |  | (_)        /  __ \                    | |        ..  ..   / o._)                   .---.
    | |  | |_ _ __ ___| /  \/ __ _ _ __ ___   ___| |       /--'/--\\  \-'||        .----.    .'     '.
    | |/\| | | '__/ _ \ |    / _` | '_ ` _ \ / _ \ |      /        \\_/ / |      .'      '..'         '-.
    \  /\  / | | |  __/ \__/\ (_| | | | | | |  __/ |    .'\\  \\__\\  __.'.'     .'          -._
     \/  \/|_|_|  \___|\____/\__,_|_| |_| |_|\___|_|      )\ |  )\ |      _.'
                                                         // \\ // \\
                                                        ||_  \\|_  \\_
                                                        '--' '--'' '--'

## Warning
Documentation is not yet finished. Fell free to contact me until it's written.

## Introduction
Wirecamel is a Python based project aimed to automate the use of SSL Split in an IoT security auditing context and
help retrieve human readable data.

The main goal is a security audit for IoTs. It creates an access point (configurable by the auditor), allowing the IoT
or the smartphone to connect to it. Then, a MITM (Man In The Middle) attack is performed to watch exchanged data. As
said previously, the result is a human readable an easy to understand by non technical professionnals.

## Installation
### Requirements
First of all, Python 2.7 and Pip are required. 

```bash
$ sudo apt-get install python-dev python-pip
$ sudo dnf install python-dev python-pip
```

Run the setup script as follow

`$ python setup.py install`

The following dependencies are required too:

```bash
# Debian based
$ sudo apt-get install aircrack-ng wireless-tools xterm dhcpd dnsmasq sslsplit whois
# Fedora
$ sudo dnf install aircrack-ng wireless-tools xterm dhcpd dnsmasq sslsplit whois
# Archlinux
$ yaourt -S aircrack-ng wireless-tools xterm dhcpd dnsmasq whois
```