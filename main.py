from api import Client, Switch, Bulb, event, Doorbell, MqttObject, Flicker

import asyncio
import random

class DefaultDoorbell(Doorbell):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb
        self._flickering = False

    @event()
    async def on_ring(self, payload):
        print('ring')
        await self.bulb.animate_toggle(Flicker())

class Button(MqttObject):
    @event('single')
    async def on_single(self, payload):
        pass

    @event('double')
    async def on_double(self, payload):
        pass


class DefaultSwitch(Switch):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb
        self._steps = 20

    @event()
    async def on_press(self, payload):
        if self.bulb.is_on():
            self.bulb.set_brightness(self.bulb.BRIGHTNESS_MAX)
        else:
            self.bulb.set_on()

    @event()
    async def off_press(self, payload):
        print('pressed')
        self.bulb.set_off()

    @event()
    async def down_press(self, payload):
        self.bulb.decrease_brightness(self._steps)

    @event()
    async def up_press(self, payload):
        self.bulb.increase_brightness(self._steps)

client = Client("192.168.2.11")

bulb1 = client.add_device(Bulb('zigbee2mqtt/Bulb 1'))
bulb2 = client.add_device(Bulb('zigbee2mqtt/Bulb 2'))
bulb3 = client.add_device(Bulb('zigbee2mqtt/Bulb 3'))

switch1 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 1', bulb1))
switch2 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 2', bulb2))
switch3 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 3', bulb3))

doorbell1 = client.add_device(DefaultDoorbell('doorbell/1', bulb1))
doorbell2 = client.add_device(DefaultDoorbell('doorbell/2', bulb1))

button1 = client.add_device(Button('zigbee2mqtt/Button 1'))
button2 = client.add_device(Button('zigbee2mqtt/Button 2'))

asyncio.run(client.start())