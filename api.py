import asyncio
import datetime
import json
import random
from typing import Dict, TypeVar, List, Optional

import paho.mqtt.client as mqtt

T = TypeVar('T')

def action(name: str = None):
    def wrapper(func):
        name2 = name or func.__name__
        func._event = Event(func, lambda x: x['action'] == name2)
        return func
    return wrapper

def event(payload_check):
    def wrapper(func):
        func._event = Event(func, payload_check)
        return func
    return wrapper


class Event:
    def __init__(self, function, payload_check):
        self.function = function
        self.payload_check = payload_check


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
        self._animation: Optional[Animation] = None
        self.history: List[History] = []
        self.events: List[Event] = list(self._get_events())
        self.context = None

    async def stop_animation(self, wait: bool = True):
        if self._animation:
            self._animation.stop()
        if wait:
            await self._wait_until_stopped()

    async def _wait_until_stopped(self):
        while self._animation:
            await asyncio.sleep(1)

    @property
    def last_state(self):
        if len(self.history) == 0:
            return {}
        return self.history[-1].payload

    async def animate_toggle(self, animation: 'Animation', duration: int = None):
        if self._animation is None:
            await self.animate(animation, duration)
        else:
            self._animation.stop()

    async def animate(self, animation: 'Animation', duration: int):
        self._animation = animation
        if self._animation.object is None:
            self._animation.object = self
        await self._animation.start(duration)
        self._animation = None

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


class Animation:
    def __init__(self, object: MqttObject = None):
        self._before = None
        self.object = object
        self._animating = False

    async def iteration(self):
        pass

    def stop(self):
        self._animating = False

    async def complete(self):
        pass

    async def start(self, duration: int = None):
        self._animating = True
        self._before = self.object.last_state
        if duration is not None:
            end = asyncio.get_event_loop().time() + duration
        else:
            end = 999999999999.0
        while asyncio.get_event_loop().time() < end and self._animating:
            await self.iteration()
        # print('done animating', asyncio.get_event_loop().time(), self._animating)
        self._animating = False
        await self.complete()


class Flicker(Animation):
    def __init__(self, bulb: 'Bulb' = None):
        super().__init__(bulb)

    async def iteration(self):
        base = 160
        if random.random() < 0.05:
            brightness = random.randint(base - 60, base)
            transition = random.uniform(0.15, 0.25)
        else:
            step = 20
            flicker = random.randint(-step, step)
            brightness = base + flicker
            transition = random.uniform(0.3, 0.5)

        self.object.set_brightness(brightness, transition)
        await asyncio.sleep(transition)

    async def complete(self):
        if not self._before:
            return
        brightness = self._before['brightness']
        state = self._before['state']
        self.object.set(BulbPayload(brightness=brightness, on=state == 'ON'))


class BulbPayload:
    __slots__ = ('brightness', 'transition', 'on')

    BRIGHTNESS_MAX = 255
    BRIGHTNESS_MIN = 0

    def __init__(self, brightness: int = None, transition: float = None, on: bool = None):
        if brightness:
            brightness = max(self.BRIGHTNESS_MIN, min(self.BRIGHTNESS_MAX, brightness))
        self.brightness = brightness
        self.transition = transition
        self.on = on

    def payload(self) -> dict:
        data = {}
        if self.brightness is not None:
            brightness = max(self.BRIGHTNESS_MIN, min(self.BRIGHTNESS_MAX, self.brightness))
            data['brightness'] = brightness
        if self.transition:
            data['transition'] = self.transition
        if self.on is not None:
            data['state'] = 'ON' if self.on else 'OFF'
        return data


class Bulb(MqttObject):
    BRIGHTNESS_MAX = 255
    BRIGHTNESS_MIN = 0

    def __init__(self, name):
        super().__init__(name)

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

    def set(self, payload: BulbPayload):
        data = payload.payload()
        if data:
            self.context.set_state(self.name, data)

    def set_brightness(self, brightness: int, transition: float = None):
        self.set(BulbPayload(brightness, transition))

    def _set_state(self, value: bool):
        self.set(BulbPayload(on=value))

    def set_on(self):
        self._set_state(True)

    def set_off(self):
        self._set_state(False)

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
        self._loop = None
        self.history: List[History] = []

    def log(self, message):
        if False:
            print(message)

    def on_connect(self, *_):
        for device in self._devices.values():
            self.client.subscribe(device.name)
            self.log('subscribed to ' + device.name)

    def add_device(self, device: T) -> T:
        device.context = self
        self._devices[device.name] = device
        return device

    def on_message(self, _, __, message):
        self.log("topic: " + message.topic + ", payload: " + str(message.payload))
        payload = json.loads(message.payload.decode())

        device = self._devices.get(message.topic)
        if device is None:
            return

        history = History(payload, datetime.datetime.now(tz=datetime.timezone.utc))
        device.history.append(history)
        self.history.append(history)

        for event in device.events:
            try:
                if event.payload_check(payload):
                    asyncio.run_coroutine_threadsafe(event.function(device, payload), self._loop)
            except:
                pass

    async def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, 1883, 60)
        self.client.loop_start()
        self._loop = asyncio.get_event_loop()
        await asyncio.Event().wait()

    def set_state(self, target, state):
        s = json.dumps(state)
        self.log('publishing ' + s)
        self.client.publish(f'{target}/set', s)

