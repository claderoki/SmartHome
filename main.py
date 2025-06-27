from api import Client, Switch, Bulb, action, Doorbell, MqttObject, Flicker, event

import asyncio

class DefaultDoorbell(Doorbell):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb
        self._flickering = False

    @action()
    async def on_ring(self, payload):
        await self.bulb.animate_toggle(Flicker())

class Button(MqttObject):
    @action('single')
    async def on_single(self, payload):
        pass

    @action('double')
    async def on_double(self, payload):
        pass

class StaticDetector(MqttObject):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb

    @event(lambda x: x['occupancy'])
    async def occupied(self, _):
        self.bulb.set_on()

    @event(lambda x: not x['occupancy'])
    async def unoccupied(self, _):
        self.bulb.set_off()

class DefaultSwitch(Switch):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb
        self._steps = 20

    @action()
    async def on_press(self, payload):
        await self.bulb.stop_animation()
        if self.bulb.is_on():
            self.bulb.set_brightness(self.bulb.BRIGHTNESS_MAX)
        else:
            self.bulb.set_on()

    @action()
    async def off_press(self, payload):
        await self.bulb.stop_animation()
        self.bulb.set_off()

    @action()
    async def down_press(self, payload):
        await self.bulb.stop_animation()
        self.bulb.decrease_brightness(self._steps)

    @action()
    async def up_press(self, payload):
        await self.bulb.stop_animation()
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
button3 = client.add_device(Button('zigbee2mqtt/Button 3'))

a = client.add_device(StaticDetector('zigbee2mqtt/Static 1', bulb3))

asyncio.run(client.start())