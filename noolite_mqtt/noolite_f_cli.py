#!/usr/bin/python3

import sys
from noolite_mqtt.noolite_serial import NooLiteSerial

noo_serial = NooLiteSerial('/dev/ttyS0')

if len(sys.argv) < 3:
    raise Exception('Not Enough params')

noo_serial.send_command(int(sys.argv[1]), int(sys.argv[2]), 2)
print(noo_serial.receive())

