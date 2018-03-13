#!/usr/bin/python3

import paho.mqtt.client as mqtt
from noolite_serial import NooLiteSerial
import re
from time import sleep
import signal
import argparse

COMMANDS = {
    'OFF': 0,
    'ON': 2,
    'SWITCH': 4,
    'BIND': 15,
}

F_COMMANDS = {
    'OFF': 0,
    'ON': 2,
    'SWITCH': 4,
    'BIND': 15,
    'GET_STATE': 128,
}


class NooLiteMQTT:
    def __init__(self, serial_device: str, mqtt_host: str,
                 mqtt_port: int, mqtt_prefix: str):
        self._noo_serial = NooLiteSerial(serial_device)

        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message

        self._mqtt_client.connect(mqtt_host, mqtt_port, 60)
        self._mqtt_prefix = mqtt_prefix

        self._exit = False

    def loop(self):
        signal.signal(signal.SIGINT, self._interrupt_handler)
        signal.signal(signal.SIGTERM, self._interrupt_handler)

        while not self._exit:
            # first receive packets from noolite serial
            packets = self._noo_serial.receive()
            for packet in packets:
                self._on_packet(packet)
            # here we run MQTT messages
            self._mqtt_client.loop()

    def _interrupt_handler(self, _signal, _frame):
        print('Exiting loop...')
        self._exit = True

    # The callback for when the client receives a CONNACK response
    def _on_connect(self, client, _userdata, _flags, rc):
        print('Connected with result code %d' % rc)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe([
            ('%s/tx/#' % self._mqtt_prefix, 0),
            ('%s/tx-f/#' % self._mqtt_prefix, 0)
        ])

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, _client, _userdata, msg):
        print(msg.topic+': '+msg.payload.decode())

        tx_match = re.match('%s/tx/(\d+)' % self._mqtt_prefix, msg.topic)
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = msg.payload.decode()
            if cmd in COMMANDS:
                self._noo_serial.send_command(ch, COMMANDS[cmd], mode=0)
                sleep(0.3)

        tx_match = re.match('%s/tx-f/(\d+)' % self._mqtt_prefix, msg.topic)
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = msg.payload.decode()
            if cmd in F_COMMANDS:
                self._noo_serial.send_command(ch, F_COMMANDS[cmd], mode=2)
                sleep(0.3)

    # The callback to call when packet received from noolite
    def _on_packet(self, packet):
        mode = packet[1]
        ch = packet[4]
        cmd = packet[5]
        self._mqtt_client.publish(
            '%s/echo/%d' % (self._mqtt_prefix, ch),
            '[%s]' % ','.join([str(b) for b in packet])
        )
        if mode == 2 and cmd == 130:
            state = packet[9] & 0x0f
            self._mqtt_client.publish(
                '%s/state-f/%d' % (self._mqtt_prefix, ch),
                'ON' if state > 0 else 'OFF',
                retain=True
            )
        elif mode == 1:
            if cmd == 25 or cmd == 2:
                self._mqtt_client.publish(
                    '%s/switch/%d' % (self._mqtt_prefix, ch),
                    'ON'
                )
            elif cmd == 0:
                self._mqtt_client.publish(
                    '%s/switch/%d' % (self._mqtt_prefix, ch),
                    'OFF'
                )
            elif cmd == 21:  # temperature & humidity sensor
                deci_temp = packet[7] | ((packet[8] & 0x0f) << 8)

                # fix for signed 12-bit values
                if deci_temp & 0x0800:
                    from ctypes import c_int16
                    deci_temp = c_int16(deci_temp | 0xf000).value

                temp = deci_temp / 10.0
                hum = packet[9]
                self._mqtt_client.publish(
                    '%s/temperature/%d' % (self._mqtt_prefix, ch),
                    '%.1f' % temp
                )
                self._mqtt_client.publish(
                    '%s/humidity/%d' % (self._mqtt_prefix, ch),
                    '%d' % hum
                )


parser = argparse.ArgumentParser()

parser.add_argument('serial_device', help='Serial device name', type=str)
parser.add_argument('mqtt_prefix', help='MQTT prefix', type=str)
parser.add_argument('mqtt_host', help='MQTT hostname', type=str)
parser.add_argument('mqtt_port', help='MQTT port', type=int,
                    nargs='?', default=1883)

args = vars(parser.parse_args())

NooLiteMQTT(**args).loop()
