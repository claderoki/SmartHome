import datetime
import json
import threading
from typing import Dict, TypeVar, List

import paho.mqtt.client as mqtt

T = TypeVar('T')

def event(name: str = None):
    def wrapper(func):
        func._event = Event(func, name or func.__name__)
        return func
    return wrapper


class Event:
    def __init__(self, function, name):
        self.function = function
        self.name = name


class History:
    def __init__(self, payload, date: datetime.datetime):
        self.payload = payload
        self.date = date


class Sequence:
    def __init__(self, action: str, max_delay_inbetween: float, wait_delay: float):
        self.action = action
        self.max_delay_inbetween = max_delay_inbetween
        self.wait_delay = wait_delay


class MqttObject:
    def __init__(self, name):
        self.name = name
        self.history: List[History] = []
        self.events: Dict[str, Event] = {x.name:x for x in self._get_events()}
        self.context = None

    def _get_events(self):
        for name in dir(self):
            attr = getattr(self, name)
            if not callable(attr):
                continue

            func = getattr(attr, '__func__', attr)
            event = getattr(func, '_event', None)
            if event:
                yield event

class Switch(MqttObject):
    def on_press_release(self, payload): pass
    def on_press(self, payload): pass
    def up_press(self, payload): pass
    def up_press_release(self, payload): pass
    def down_press(self, payload): pass
    def down_press_release(self, payload): pass
    def off_press(self, payload): pass
    def off_press_release(self, payload): pass


class Doorbell(MqttObject):
    def on_ring(self, payload): pass


class Bulb(MqttObject):
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
        self.context.set_state(self.name, {'brightness': brightness})

    def _set_state(self, value: bool):
        self.context.set_state(self.name, {"state": 'ON' if value else 'OFF'})

    def set_on(self):
        self._set_state(True)

    def is_on(self):
        last_state = self.last_known_state.get('state')
        if last_state is None:
            return False
        return last_state == 'ON'

    def _handle_sequence(self):
        pass

    def _get_current_brightness(self):
        return self.last_known_state.get('brightness', 125)

    def is_off(self):
        return not self.is_on()

    def set_off(self):
        self._set_state(False)

    def toggle(self):
        if self.is_on():
            self.set_off()
        else:
            self.set_on()


class Client:
    def __init__(self, host):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.host = host
        self._devices: Dict[str, MqttObject] = {}
        self._last_known_states: dict = {}
        self.history: List[History] = []

    def on_connect(self, *_):
        for device in self._devices.values():
            self.client.subscribe(device.name)

    def add_device(self, device: T) -> T:
        device.context = self
        self._devices[device.name] = device
        return device

    def on_message(self, _, __, message):
        print("topic: " + message.topic + ", payload: " + str(message.payload))
        payload = json.loads(message.payload.decode())

        device = self._devices.get(message.topic)
        if device is None:
            return

        history = History(payload, datetime.datetime.now(tz=datetime.timezone.utc))
        device.history.append(history)
        self.history.append(history)

        action = payload.get('action')
        event = device.events.get(action)
        if event is None:
            return

        event.function(device, payload)


    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, 1883, 60)
        self.client.loop_forever()


    def set_state(self, target, state):
        self.client.publish(f'{target}/set', json.dumps(state))

