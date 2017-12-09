#!/usr/bin/env python
# coding=utf-8
import sys
import getpass

from WirecamelInteractive import WirecamelInteractive


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # Checking if running as root
    if 'root' != getpass.getuser():
        print("Must have root privileges. Aborting.")
        exit(1)

    # Running main script
    WirecamelInteractive().cmdloop()


if __name__ == "__main__":
    main()
