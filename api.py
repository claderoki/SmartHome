import datetime
import json
from typing import Dict, List

import paho.mqtt.client as mqtt

class History:
    def __init__(self, payload, date: datetime.datetime):
        self.payload = payload
        self.date = date


class ZigbeeObject:
    def __init__(self, context, name):
        self._context = context
        self.name = name
        self.history: List[History] = []

class Switch(ZigbeeObject):
    def on_press_release(self, payload): pass
    def on_press(self, payload): pass
    def up_press(self, payload): pass
    def up_press_release(self, payload): pass
    def down_press(self, payload): pass
    def down_press_release(self, payload): pass
    def off_press(self, payload): pass
    def off_press_release(self, payload): pass


class Bulb(ZigbeeObject):
    BRIGHTNESS_MAX = 255
    BRIGHTNESS_MIN = 0

    @property
    def last_known_state(self):
        if len(self.history) == 0:
            return {}
        return self.history[-1].payload

    def decrease_brightness(self, by: int):
        brightness = self._get_current_brightness()
        self.set_brightness(brightness - by)

    def increase_brightness(self, by: int):
        brightness = self._get_current_brightness()
        self.set_brightness(brightness + by)

    def set_brightness(self, brightness: int):
        brightness = max(self.BRIGHTNESS_MIN, min(self.BRIGHTNESS_MAX, brightness))
        self._context.set_state(self.name, {'brightness': brightness})

    def _set_state(self, value: bool):
        self._context.set_state(self.name, {"state": 'ON' if value else 'OFF'})

    def set_on(self):
        self._set_state(True)

    def is_on(self):
        last_state = self.last_known_state.get('state')
        if last_state is None:
            return False
        return last_state == 'ON'

    def _get_current_brightness(self):
        return self.last_known_state.get('brightness', 125)

    def is_off(self):
        return not self.is_on()

    def set_off(self):
        self._set_state(False)


class Context:
    def __init__(self, host):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.host = host
        self._cached_devices: Dict[str, ZigbeeObject] = {}
        self._last_known_states: dict = {}
        self.history: List[History] = []

    def on_connect(self, *_):
        for device in self._cached_devices.values():
            self.client.subscribe(device.name)

    def add_device(self, device: ZigbeeObject) -> ZigbeeObject:
        self._cached_devices[device.name] = device
        return device

    def on_message(self, _, __, message):
        payload = json.loads(message.payload.decode())

        device = self._cached_devices.get(message.topic)
        if device is None:
            return

        history = History(payload, datetime.datetime.now(tz=datetime.timezone.utc))
        device.history.append(history)
        self.history.append(history)

        action = payload.get('action')
        if isinstance(device, Switch) and action is not None:
            if hasattr(device, action):
                getattr(device, action)(payload)

        print("topic: " + message.topic + ", payload: " + str(message.payload))

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, 1883, 60)
        self.client.loop_forever()


    def set_state(self, target, state):
        self.client.publish(f'{target}/set', json.dumps(state))

