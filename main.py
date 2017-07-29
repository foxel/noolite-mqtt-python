#!/usr/bin/python2.7

import paho.mqtt.client as mqtt
from noolite_serial import NooLiteSerial
import re
from time import sleep

PREFIX = 'foxhome/noolite'

COMMANDS_MAP = {
    'OFF': 0,
    'ON': 2,
    'SWITCH': 4,
    'BIND': 15,
    'GET_STATE': 128,
}


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print('Connected with result code %d' % rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe([('%s/tx/#' % PREFIX, 0), ('%s/tx-f/#' % PREFIX, 0)])


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+": "+str(msg.payload))

    tx_match = re.match('%s/tx/(\d+)' % PREFIX, msg.topic)
    if tx_match:
        ch = int(tx_match.group(1))
        cmd = str(msg.payload)
        if cmd in COMMANDS_MAP:
            noo_serial.send_command(ch, COMMANDS_MAP[cmd], mode=0)
            sleep(0.3)

    tx_match = re.match('%s/tx-f/(\d+)' % PREFIX, msg.topic)
    if tx_match:
        ch = int(tx_match.group(1))
        cmd = str(msg.payload)
        if cmd in COMMANDS_MAP:
            noo_serial.send_command(ch, COMMANDS_MAP[cmd], mode=2)
            sleep(0.3)


noo_serial = NooLiteSerial('/dev/ttyS0')

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect('127.0.0.1', 1883, 60)

run = True
while run:
    resp = noo_serial.receive()
    if len(resp):
        ch = ord(resp[0][4])
        cmd = ord(resp[0][5])
        mqtt_client.publish(
            '%s/echo/%d' % (PREFIX, ch),
            '[%s]' % '|'.join([','.join([str(ord(b)) for b in r]) for r in resp])
        )
        if cmd == 130:
            state = ord(resp[0][9]) & 0x0f
            mqtt_client.publish(
                '%s/state-f/%d' % (PREFIX, ch),
                'ON' if state > 0 else 'OFF',
                retain=True
            )
    mqtt_client.loop()
