# coding=utf-8
import subprocess
import dnsmasq


# Kill unwanted processes for the spawn of an AP
def kill_unwanted():
    return subprocess.call('airmon-ng check kill'.split(' '), stdout=subprocess.PIPE)


# Check if devices are blocked and unblock if needed
def check_rfkill():
    return subprocess.call('rfkill unblock wifi'.split(' '), stdout=subprocess.PIPE)


# Enable ip forwarding
def ip_forward(enable):
    # Creating the command, depending if the user want it enabled or not
    command = "sysctl -w net.ipv4.ip_forward={}"
    command = command.format('1') if enable else command.format('0')

    # Executing the command and returning the result
    return subprocess.call(command.split(" "), stdout=subprocess.PIPE)


# Set router ip
def configure_interface(interface):
    return subprocess.call(
        ['ifconfig', interface, dnsmasq.ROUTER_IP, 'up'],
        stdout=subprocess.PIPE
    )
