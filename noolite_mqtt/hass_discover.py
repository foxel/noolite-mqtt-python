import argparse
import json
from typing import Dict, List

import paho.mqtt.client as mqtt

DISCOVERY_PREFIX = 'homeassistant'


def discovery_topic(entity_type: str, entity_id: str) -> str:
    return '%s/%s/%s/config' % (DISCOVERY_PREFIX, entity_type, entity_id)


def push_discovery(client: mqtt.Client, entity_type: str, entity_name: str, data: Dict):
    print('adding ' + entity_name)
    client.publish(
        discovery_topic(entity_type, entity_name),
        json.dumps({'name': entity_name, **data}),
        retain=True,
    )


def device(root_id: str, id: str, name: str, manufacturer: str = 'NooLite') -> Dict:
    return {
        'device': {
            'identifiers': [id],
            'manufacturer': manufacturer,
            'name': name,
            'via_device': root_id,
        }
    }


def lwt(mqtt_prefix: str) -> Dict:
    return {
        'availability_topic': '%s/LWT' % mqtt_prefix,
        'payload_available': 'Online',
        'payload_not_available': 'Offline',
    }


def push_noolite_root_device(client: mqtt.Client, mqtt_prefix: str, root_id: str):
    push_discovery(
        client, 'binary_sensor', root_id,
        {
            'name': 'NooLite MQTT Bridge Status',
            'state_topic': '%s/LWT' % mqtt_prefix,
            'payload_on': 'Online',
            'payload_off': 'Offline',
            'unique_id': root_id,
            'device_class': 'connectivity',
            'device': {
                'identifiers': [root_id],
                'manufacturer': 'NooLite',
                'name': 'NooLite MTRF64',
            },
        }
    )


def push_pm112(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    push_discovery(
        client, 'binary_sensor', 'noolite_motion_%d' % channel,
        {
            'state_topic': '%s/switch/%d' % (mqtt_prefix, channel),
            'payload_on': 'ON',
            'device_class': 'motion',
            'off_delay': '180',
            'unique_id': '%s_motion' % device_id,
            **device(root_id, device_id, 'PM112 Motion Sensor'),
            **lwt(mqtt_prefix),
        }
    )


def push_pt111(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    common = {
        **device(root_id, device_id, 'PT111 Temperature and Humidity Sensor'),
        **lwt(mqtt_prefix),
    }
    push_discovery(
        client, 'sensor', 'noolite_temperature_%d' % channel,
        {
            'state_topic': '%s/temperature/%d' % (mqtt_prefix, channel),
            'expire_after': 3700,
            'force_update': True,
            'device_class': 'temperature',
            'unit_of_measurement': '°C',
            'unique_id': '%s_temperature' % device_id,
            **common,
        }
    )
    push_discovery(
        client, 'sensor', 'noolite_humidity_%d' % channel,
        {
            'state_topic': '%s/humidity/%d' % (mqtt_prefix, channel),
            'expire_after': 3700,
            'force_update': True,
            'device_class': 'humidity',
            'unit_of_measurement': '%',
            'unique_id': '%s_humidity' % device_id,
            **common,
        }
    )


def push_pt112(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    push_discovery(
        client, 'sensor', 'noolite_temperature_%d' % channel,
        {
            'state_topic': '%s/temperature/%d' % (mqtt_prefix, channel),
            'expire_after': 3700,
            'force_update': True,
            'device_class': 'temperature',
            'unit_of_measurement': '°C',
            'unique_id': '%s_temperature' % device_id,
            **device(root_id, device_id, 'PT112 Temperature Sensor'),
            **lwt(mqtt_prefix),
        }
    )


def push_pl111(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    push_discovery(
        client, 'binary_sensor', 'noolite_light_%d' % channel,
        {
            'state_topic': '%s/switch/%d' % (mqtt_prefix, channel),
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'device_class': 'light',
            'unique_id': '%s_light' % device_id,
            **device(root_id, device_id, 'PL111 Light Sensor'),
            **lwt(mqtt_prefix),
        }
    )


def push_ds1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    push_discovery(
        client, 'binary_sensor', 'noolite_open_%d' % channel,
        {
            'state_topic': '%s/switch/%d' % (mqtt_prefix, channel),
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'device_class': 'opening',
            'unique_id': '%s_open' % device_id,
            **device(root_id, device_id, 'DS-1 Open Sensor'),
            **lwt(mqtt_prefix),
        }
    )


def push_ws1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    push_discovery(
        client, 'binary_sensor', 'noolite_water_%d' % channel,
        {
            'state_topic': '%s/switch/%d' % (mqtt_prefix, channel),
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'device_class': 'moisture',
            'unique_id': '%s_water' % device_id,
            **device(root_id, device_id, 'WS-1 Water Sensor'),
            **lwt(mqtt_prefix),
        }
    )


def push_pxx(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int, *,
             channel2: int = None, channel3: int = None, channel4: int = None, mode: str = 'switch'):

    device_id = '%s_rx_%d' % (root_id, channel)
    channels = [channel, channel2, channel3, channel4]

    for ch in channels:
        if ch is None:
            continue

        if mode == 'switch':
            push_discovery(
                client, 'binary_sensor', 'noolite_switch_%d' % ch,
                {
                    'state_topic': '%s/switch/%d' % (mqtt_prefix, ch),
                    'payload_on': 'ON',
                    'payload_off': 'OFF',
                    'unique_id': '%s_rx_%d_switch' % (root_id, ch),
                    **device(root_id, device_id, 'PX-XXX Remote Switch'),
                    **lwt(mqtt_prefix),
                }
            )
        elif mode == 'button':
            push_discovery(
                client, 'binary_sensor', 'noolite_button_%d' % ch,
                {
                    'state_topic': '%s/button/%d' % (mqtt_prefix, ch),
                    'payload_on': 'TOGGLE',
                    'off_delay': 1,
                    'unique_id': '%s_rx_%d_button' % (root_id, ch),
                    **device(root_id, device_id, 'PX-XXX Remote Button'),
                    **lwt(mqtt_prefix),
                }
            )
        else:
            raise TypeError('PXX mode should be either switch or button')


def push_sr1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int, *, mode: str = 'switch'):
    device_id = '%s_tx_%d' % (root_id, channel)
    if mode == 'switch' or mode == 'light':
        push_discovery(
            client, mode, 'noolite_switch_%d' % channel,
            {
                'command_topic': '%s/tx/%d' % (mqtt_prefix, channel),
                'unique_id': '%s_switch' % device_id,
                **device(root_id, device_id, 'SR-1-X Switch'),
                **lwt(mqtt_prefix),
            }
        )
    else:
        raise TypeError('SR1 mode should be either switch or light')


def push_su1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int, *, mode: str = 'light'):
    push_sr1(client, mqtt_prefix, root_id, channel, mode=mode)


def push_srf1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int, *, mode: str = 'switch'):
    device_id = '%s_txf_%d' % (root_id, channel)
    if mode == 'switch' or mode == 'light':
        push_discovery(
            client, mode, 'noolite_switch_%d' % channel,
            {
                'command_topic': '%s/tx-f/%d' % (mqtt_prefix, channel),
                'state_topic': '%s/state-f/%d' % (mqtt_prefix, channel),
                'unique_id': '%s_switch' % device_id,
                **device(root_id, device_id, 'SRF-1-X Switch'),
                **lwt(mqtt_prefix),
            }
        )
    else:
        raise TypeError('SRF1 mode should be either switch or light')


def push_suf1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int, *, mode: str = 'light'):
    push_srf1(client, mqtt_prefix, root_id, channel, mode=mode)


def push_foxel_sensor_1(client: mqtt.Client, mqtt_prefix: str, root_id: str, channel: int):
    device_id = '%s_rx_%d' % (root_id, channel)
    common = {
        'expire_after': 600,
        'force_update': True,
        **device(root_id, device_id, 'Foxel\'s NooLite Sensor', 'Foxel'),
        **lwt(mqtt_prefix),
    }
    push_discovery(
        client, 'binary_sensor', 'noolite_motion_%d' % channel,
        {
            'state_topic': '%s/switch/%d' % (mqtt_prefix, channel),
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'device_class': 'motion',
            'off_delay': '180',
            'unique_id': '%s_motion' % device_id,
            **device(root_id, device_id, 'Foxel\'s NooLite Sensor', 'Foxel'),
            **lwt(mqtt_prefix),
        }
    )
    push_discovery(
        client, 'sensor', 'noolite_temperature_%d' % channel,
        {
            'state_topic': '%s/temperature/%d' % (mqtt_prefix, channel),
            'device_class': 'temperature',
            'unit_of_measurement': '°C',
            'unique_id': '%s_temperature' % device_id,
            **common,
        }
    )
    push_discovery(
        client, 'sensor', 'noolite_humidity_%d' % channel,
        {
            'state_topic': '%s/humidity/%d' % (mqtt_prefix, channel),
            'device_class': 'humidity',
            'unit_of_measurement': '%',
            'unique_id': '%s_humidity' % device_id,
            **common,
        }
    )
    push_discovery(
        client, 'sensor', 'noolite_battery_%d' % channel,
        {
            'state_topic': '%s/battery/%d' % (mqtt_prefix, channel),
            'device_class': 'battery',
            'unit_of_measurement': 'V',
            'unique_id': '%s_battery' % device_id,
            **common,
        }
    )


device_push = {
    'pm112': push_pm112,
    'pt111': push_pt111,
    'pt112': push_pt112,
    'pl111': push_pl111,
    'ds1': push_ds1,
    'ws1': push_ws1,
    'sr1': push_sr1,
    'su1': push_su1,
    'sb1': push_su1,
    'srf1': push_srf1,
    'suf1': push_suf1,
    'pxx': push_pxx,
    'fox1': push_foxel_sensor_1,
}


def send_discovery(
        devices: List[Dict],
        mqtt_host: str,
        mqtt_port: int,
        mqtt_prefix: str,
        username: str = None,
        password: str = None
):

    def on_disconnect(_client: mqtt.Client, _user_data, rc: int):
        if rc != 0:
            print("Unexpected disconnection.")

    mqtt_client = mqtt.Client()
    mqtt_client.on_disconnect = on_disconnect

    if username is not None and username != '':
        mqtt_client.username_pw_set(username, password)

    mqtt_client.connect(mqtt_host, mqtt_port, 60)

    mqtt_client.loop_start()

    root_id = mqtt_prefix.replace('/', '_')

    push_noolite_root_device(mqtt_client, mqtt_prefix, root_id)
    for device_info in devices:
        device_info = dict(device_info)
        device_type = str(device_info.pop('type'))
        device_push[device_type](mqtt_client, mqtt_prefix, root_id, **device_info)

    mqtt_client.loop_stop()
    mqtt_client.disconnect()


def json_list(value: str) -> List:
    return list(json.loads(value))


def cli():
    parser = argparse.ArgumentParser()

    parser.add_argument('mqtt_prefix', help='MQTT prefix', type=str)
    parser.add_argument('mqtt_host', help='MQTT hostname', type=str)
    parser.add_argument('username', help='MQTT user name', type=str, nargs='?', default=None)
    parser.add_argument('password', help='MQTT user password', type=str, nargs='?', default=None)
    parser.add_argument('-p', '--mqtt_port', help='MQTT port', type=int, nargs='?', default=1883)
    parser.add_argument('-d', '--devices', help='devices to discover', type=json_list, required=True)

    args = vars(parser.parse_args())

    send_discovery(**args)


if __name__ == '__main__':
    cli()
