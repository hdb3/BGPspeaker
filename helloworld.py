#!/usr/bin/env python
import sys
assert sys.version_info > (3,5)
#from ipaddress import IPv4Address
import netifaces

from sessionmanager import SessionManager

def get_local_ipv4_addresses():
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            for address_info in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                yield address_info['addr']

peers = ["192.168.122.1","192.168.122.179","192.168.122.113"]
local_addresses = list(get_local_ipv4_addresses())
#print(local_addresses)
#print(peers)
_peers = []
for peer in peers:
    if peer not in local_addresses:
        print("using %s" % peer)
        _peers.append(peer)

# __peers = list(map(IPv4Address,_peers))
sm = SessionManager(_peers)
