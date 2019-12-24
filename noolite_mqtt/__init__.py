import argparse
import re
import signal
from time import sleep, monotonic as time

import paho.mqtt.client as mqtt

from noolite_mqtt.noolite_serial import NooLiteSerial
from .enums import Command, Mode, Request

COMMANDS = {
    'OFF': Command.OFF,
    'ON': Command.ON,
    'SWITCH': Command.TOGGLE,
    'TOGGLE': Command.TOGGLE,
    'BIND': Command.BIND,
    'UNBIND': Command.UNBIND,
}

COMMANDS_FMT1 = {
    'BRIGHTNESS': Command.BRIGHT_SET,
}

F_COMMANDS = {
    'OFF': Command.OFF,
    'ON': Command.ON,
    'SWITCH': Command.TOGGLE,
    'TOGGLE': Command.TOGGLE,
    'BIND': Command.BIND,
    'UNBIND': Command.UNBIND,
    'GET_STATE': Command.READ_STATE,
}

F_COMMANDS_FMT1 = {
    'BRIGHTNESS': Command.BRIGHT_SET,
}

BOOLEANS = {
    '1': True,
    'ON': True,
    '0': False,
    'OFF': False,
}


class NooLiteMQTT:
    def __init__(self, serial_device: str, mqtt_host: str,
                 mqtt_port: int, mqtt_prefix: str,
                 username: str=None, password: str=None):
        self._noo_serial = NooLiteSerial(serial_device)

        self._mqtt_prefix = mqtt_prefix

        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message

        if username is not None and username != '':
            self._mqtt_client.username_pw_set(username, password)

        self._postponed = []

        self._exit = False

        self._mqtt_client.will_set('%s/LWT' % self._mqtt_prefix, 'Offline', 0, True)
        self._mqtt_client.connect(mqtt_host, mqtt_port, 60)

    def loop(self):
        signal.signal(signal.SIGINT, self._interrupt_handler)
        signal.signal(signal.SIGTERM, self._interrupt_handler)

        self._mqtt_client.publish('%s/LWT' % self._mqtt_prefix, 'Online', 0, True)

        while not self._exit:
            # first receive packets from noolite serial
            packets = self._noo_serial.receive()
            for packet in packets:
                self._on_packet(packet)

            # here we work with postponed messages
            postponed = []
            for (trigger_time, topic, payload) in self._postponed:
                if trigger_time < time():
                    self._mqtt_client.publish(topic, payload)
                else:
                    postponed.append((trigger_time, topic, payload))
            self._postponed = postponed

            # here we run MQTT loop
            self._mqtt_client.loop()

    def _interrupt_handler(self, _signal, _frame):
        print('Exiting loop...')
        self._exit = True

    # The callback for when the client receives a CONNACK response
    def _on_connect(self, client: mqtt.Client, _user_data, _flags, rc: int):
        print('Connected with result code %d' % rc)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe([
            ('%s/tx/#' % self._mqtt_prefix, 0),
            ('%s/tx-f/#' % self._mqtt_prefix, 0),
            ('%s/bind/#' % self._mqtt_prefix, 0),
            ('%s/bind-f/#' % self._mqtt_prefix, 0)
        ])

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, _client: mqtt.Client, _user_data, msg: mqtt.MQTTMessage):
        print(msg.topic + ': ' + msg.payload.decode())

        tx_match = re.match('%s/tx/(\\d+)' % self._mqtt_prefix, msg.topic)
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = msg.payload.decode()
            if cmd in COMMANDS:
                self._noo_serial.send_command(ch, COMMANDS[cmd], mode=Mode.TX)
                sleep(0.3)

        tx_match = re.match('%s/tx-f/(\\d+)' % self._mqtt_prefix, msg.topic)
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = msg.payload.decode()
            if cmd in F_COMMANDS:
                self._noo_serial.send_command(ch, F_COMMANDS[cmd], mode=Mode.TX_F)
                sleep(0.3)

        tx_match = re.match(
            '%s/tx/(\\d+)/([A-Z]+)' % self._mqtt_prefix, msg.topic
        )
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = str(tx_match.group(2))
            if cmd in COMMANDS_FMT1:
                arg = int(msg.payload.decode())
                self._noo_serial.send_command(ch, COMMANDS_FMT1[cmd], mode=Mode.TX, fmt=1, d0=arg)
                sleep(0.3)

        tx_match = re.match(
            '%s/tx-f/(\\d+)/([A-Z]+)' % self._mqtt_prefix, msg.topic
        )
        if tx_match:
            ch = int(tx_match.group(1))
            cmd = str(tx_match.group(2))
            if cmd in F_COMMANDS_FMT1:
                arg = int(msg.payload.decode())
                self._noo_serial.send_command(ch, F_COMMANDS_FMT1[cmd], mode=Mode.TX_F, fmt=1, d0=arg)
                sleep(0.3)

        # RX BIND
        bind_match = re.match('%s/bind/(\\d+)' % self._mqtt_prefix, msg.topic)
        if bind_match:
            ch = int(bind_match.group(1))
            bind_en = msg.payload.decode()
            if bind_en in BOOLEANS:
                self._noo_serial.send_command(
                    ch,
                    Command.OFF,
                    mode=Mode.RX,
                    ctr=Request.BIND_START if BOOLEANS[bind_en] else Request.BIND_STOP
                )
                sleep(0.3)

        bind_match = re.match('%s/bind-f/(\\d+)' % self._mqtt_prefix, msg.topic)
        if bind_match:
            ch = int(bind_match.group(1))
            bind_en = msg.payload.decode()
            if bind_en in BOOLEANS:
                self._noo_serial.send_command(
                    ch,
                    Command.OFF,
                    mode=Mode.RX_F,
                    ctr=Request.BIND_START if BOOLEANS[bind_en] else Request.BIND_STOP
                )
                sleep(0.3)

    # The callback to call when packet received from noolite
    def _on_packet(self, packet: bytes):
        mode = packet[1]
        ch = packet[4]
        cmd = packet[5]
        self._mqtt_client.publish(
            '%s/echo/%d' % (self._mqtt_prefix, ch),
            '[%s]' % ','.join([str(b) for b in packet])
        )
        if mode == Mode.TX_F:  # nooLite-F state case
            if cmd == Command.SEND_STATE:  # switch state
                state = packet[9] & 0x0f
                brightness = packet[10] & 0xff
                self._mqtt_client.publish(
                    '%s/state-f/%d' % (self._mqtt_prefix, ch),
                    'ON' if state > 0 else 'OFF',
                    retain=True
                )
                self._mqtt_client.publish(
                    '%s/state-f/%d/brightness' % (self._mqtt_prefix, ch),
                    str(brightness),
                    retain=True
                )
        elif mode == Mode.RX or mode == Mode.RX_F:  # regular command
            if cmd == Command.TEMPORARY_ON or cmd == Command.ON or cmd == Command.OFF:  # switch and motion detector
                switch_topic = '%s/switch/%d' % (self._mqtt_prefix, ch)
                self._mqtt_client.publish(
                    switch_topic,
                    'ON' if cmd != Command.OFF else 'OFF'
                )
                # remove any pending postponed message to this switch
                self._postponed = [
                    (trigger_time, topic, payload)
                    for (trigger_time, topic, payload) in self._postponed
                    if topic != switch_topic
                ]
                # set postponed message for motion detector
                if cmd == Command.TEMPORARY_ON:
                    interval = packet[7] * 5
                    self._postponed.append((time() + interval, switch_topic, 'OFF'))

            elif cmd == Command.SENSOR_TEMP_HUM:  # temperature & humidity sensor
                deci_temp = packet[7] | ((packet[8] & 0x0f) << 8)

                # fix for signed 12-bit values
                if deci_temp & 0x0800:
                    from ctypes import c_int16
                    deci_temp = c_int16(deci_temp | 0xf000).value

                temp = deci_temp / 10.0
                hum = packet[9]
                battery = packet[10] / 50.0  # very custom, original PT111 sends 255 value here always
                self._mqtt_client.publish(
                    '%s/temperature/%d' % (self._mqtt_prefix, ch),
                    '%.1f' % temp
                )
                self._mqtt_client.publish(
                    '%s/humidity/%d' % (self._mqtt_prefix, ch),
                    '%d' % hum
                )
                self._mqtt_client.publish(
                    '%s/battery/%d' % (self._mqtt_prefix, ch),
                    '%.2f' % battery
                )

            elif cmd == Command.BATTERY_LOW:  # low battery
                self._mqtt_client.publish(
                    '%s/battery/%d' % (self._mqtt_prefix, ch),
                    'LOW'
                )


def cli():
    parser = argparse.ArgumentParser()

    parser.add_argument('serial_device', help='Serial device name', type=str)
    parser.add_argument('mqtt_prefix', help='MQTT prefix', type=str)
    parser.add_argument('mqtt_host', help='MQTT hostname', type=str)
    parser.add_argument('username', help='MQTT user name', type=str,
                        nargs='?', default=None)
    parser.add_argument('password', help='MQTT user password', type=str,
                        nargs='?', default=None)
    parser.add_argument('-p', '--mqtt_port', help='MQTT port', type=int,
                        nargs='?', default=1883)

    args = vars(parser.parse_args())

    NooLiteMQTT(**args).loop()


if __name__ == '__main__':
    cli()
