#!/usr/bin/env python
import sys
assert sys.version_info > (3,5)
from ipaddress import IPv4Address
import netifaces

from sessionmanager import SessionManager

def get_local_ipv4_addresses():
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            for address_info in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                yield address_info['addr']

peers = ["172.16.0.1", "172.16.0.2","172.16.0.3","172.16.0.4"]
local_addresses = get_local_ipv4_addresses()
_peers = list(map(IPv4Address,peers))
__peers = []
for _peer in _peers:
    if _peer not in local_addresses:
        print("using %s" % _peer)
        __peers.append(_peer)

sm = SessionManager(__peers,10.0)
