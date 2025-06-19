import json

import paho.mqtt.client as mqtt

subscribe_to = [
    "zigbee2mqtt/Switch 1",
    "zigbee2mqtt/Switch 2",
    "zigbee2mqtt/Switch 3",
    "zigbee2mqtt/Bulb 1",
    "zigbee2mqtt/Bulb 2",
]


class Context:
    def __init__(self, client, host):
        self.client = client
        self.host = host
        self.last_known_states = {}

    def on_connect(self, *_):
        for subscription in subscribe_to:
            self.client.subscribe(subscription)

    def on_message(self, _, __, message):
        payload = json.loads(message.payload.decode())
        if "Switch" in message.topic:
            self.default_switch_bulb_action(payload, message.topic.replace("Switch", "Bulb"))

        self.last_known_states[message.topic] = payload

        print("topic: " + message.topic + ", payload: " + str(message.payload))

    def loop(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, 1883, 60)
        self.client.loop_forever()

    def set_state(self, target, state):
        self.client.publish(f'{target}/set', json.dumps(state))

    def default_switch_bulb_action(self, payload, target):
        step = 10
        last_known = self.last_known_states.get(target)
        if last_known is None:
            last_known = {'brightness': 125, 'state': 'OFF'}
        if 'action' not in payload:
            return

        if payload['action'] == 'on_press_release':
            self.set_state(target, {"state": 'OFF' if last_known['state'] == 'ON' else 'ON'})
        elif payload['action'] in ('up_press', 'up_hold'):
            self.set_state(target, {"brightness": brightness(last_known['brightness'] + step)})
        elif payload['action'] in ('down_press', 'down_hold'):
            self.set_state(target, {"brightness": brightness(last_known['brightness'] - step)})



def brightness(brightness):
    return max(0, min(255, brightness))

context = Context(mqtt.Client(mqtt.CallbackAPIVersion.VERSION2), "192.168.2.11")
context.loop()
