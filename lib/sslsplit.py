# coding=utf-8
import os
import style
import subprocess

from os.path import isfile


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
