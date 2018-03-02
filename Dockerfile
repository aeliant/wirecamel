FROM debian:stable-slim
MAINTAINER Hamza ESSAYEGH <hamza.essayegh@protonmail.com>

RUN set -x && \
    apt-get update && \
    apt-get install -y python-dev python-pip hostapd sslsplit dhcpd dnsmasq \
    aircrack-ng wireless-tools whois

COPY wirecamel /data
COPY requirements.txt /data
WORKDIR /data

RUN set -x && \
    pip install -r requirements.txt

WORKDIR /data/wirecamel

ENTRYPOINT ["python"]
CMD ["__main__.py"]