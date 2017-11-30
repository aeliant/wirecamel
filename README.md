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

## Introduction
Wirecamel is a Python based project aimed to automate the use of SSL Split in an IoT security auditing context and
help retrieve human readable data.

The main goal is a security audit for IoTs. It creates an access point (configurable by the auditor), allowing the IoT
or the smartphone to connect to it. Then, a MITM (Man In The Middle) attack is performed to watch exchanged data. As
said previously, the result is a human readable an easy to understand by non technical professionnals.

## Installation
### Requirements
First of all, Python 2.7 and Pip are required. Follow the next instructions to install required dependencies :

`$ pip install iso8601 whois tabulate python-dateutil`

For the rest, the script check unmet dependencies and ask the user to install it (on a Debian based system, other Linux
distributions are not handled yet).