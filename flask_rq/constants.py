import os
import socket
import struct


def get_default_gateway():
    route_path = "/proc/net/route"
    if os.path.isfile(route_path) is False:
        return None
    with open(route_path) as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != "00000000" or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


HOSTNAME = socket.gethostname()
GATEWAY = get_default_gateway()
