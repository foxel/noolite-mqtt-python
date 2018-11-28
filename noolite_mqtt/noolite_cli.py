#!/usr/bin/python3

import sys
from noolite_mqtt.noolite_serial import NooLiteSerial

noo_serial = NooLiteSerial('/dev/ttyS0')

if len(sys.argv) < 3:
    raise Exception('Not Enough params')

noo_serial.send_command(int(sys.argv[1]), int(sys.argv[2]), 0)
print(noo_serial.receive())

# ch, cmd, mode, ctr
# print noo_serial.send_command(0, 15, 0, 0) #1
# noo_serial.send_command(1, 4, 2, 0) #switch
# noo_serial.send_command(0, 0, 0, 0) #turn on
# noo_serial.send_command(0, 3, 2, 0) #
# noo_serial.send_command(1, 0, 0, 0) #turn off
# noo_serial.send_command(0, 15, 2, 0) #
# noo_serial.send_command(0, 128, 2, 0,0,1) #CMD_Read_State + fmt = 1
# noo_serial.on(0)
# noo_serial.status(0)
# noo_serial.off(0)
# noo_serial.off(0)
# noo_serial.status(0)
# noo_serial.send_command(ch=0,ctr=8, cmd=4, id0=0,id1=0,id2=48,id3=114) #switch noolite ID 0.0.48.114
