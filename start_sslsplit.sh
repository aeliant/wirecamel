#!/bin/bash
sslsplit -D -l connections.log -S sslsplit-logs/ -k sslsplit-keys/ca.key -c sslsplit-keys/ca.crt ssl 0.0.0.0 8443 tcp 0.0.0.0 8080
