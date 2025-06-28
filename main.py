

from api import Client, Switch, Bulb, action, Doorbell, MqttObject, Flicker, event, IkeaBulb

import asyncio

class DefaultDoorbell(Doorbell):
    def __init__(self, name, bulb: Bulb = None):
        super().__init__(name)
        self.bulb = bulb
        self._flickering = False

    @action()
    async def on_ring(self, payload):
        if self.bulb:
            await self.bulb.animate_toggle(Flicker())

class Button(MqttObject):
    def __init__(self, name):
        super().__init__(name)


class ButtonLink(MqttObject):
    def __init__(self, name, object: 'MqttObject', method):
        super().__init__(name)
        self.object = object
        self.method = method

    @action('single')
    async def on_single(self, payload):
        m = getattr(self.object, self.method)
        print(m)
        m()



class SocketButton(Button):
    def __init__(self, name, socket: 'Socket'):
        super().__init__(name)
        self.socket = socket

    @action('single')
    async def on_single(self, payload):
        await self.socket.toggle()

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


class DoorDetector(MqttObject):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb

    @event(lambda x: x['contact'])
    async def on_contact(self, _):
        self.bulb.set_on()

    @event(lambda x: not x['contact'])
    async def on_contact_off(self, _):
        self.bulb.set_off()


class Socket(MqttObject):
    def __init__(self, name):
        super().__init__(name)

    async def turn_on(self):
        self.set({'state': 'ON'})

    async def turn_off(self):
        self.set({'state': 'OFF'})

    async def toggle(self):
        state = self.last_state.get('state', 'OFF')
        if state == 'OFF':
            await self.turn_on()
        else:
            await self.turn_off()


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
bulb4 = client.add_device(IkeaBulb('zigbee2mqtt/Bulb 4'))
bulb5 = client.add_device(IkeaBulb('zigbee2mqtt/Bulb 5'))
tiny1 = client.add_device(IkeaBulb('zigbee2mqtt/Tiny bulb 1'))

switch1 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 1', bulb4))
switch2 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 2', bulb5))
switch3 = client.add_device(DefaultSwitch('zigbee2mqtt/Switch 3', bulb3))

doorbell1 = client.add_device(DefaultDoorbell('doorbell/1'))
doorbell2 = client.add_device(DefaultDoorbell('doorbell/2', bulb4))

socket1 = client.add_device(Socket('zigbee2mqtt/Socket 1'))

button1 = client.add_device(ButtonLink('zigbee2mqtt/Button 1', tiny1, 'toggle'))
button2 = client.add_device(Button('zigbee2mqtt/Button 2'))
button3 = client.add_device(SocketButton('zigbee2mqtt/Button 3', socket1))

a = client.add_device(StaticDetector('zigbee2mqtt/Static 1', bulb3))
b = client.add_device(MqttObject('zigbee2mqtt/Door 1'))

# import threading
# from flask import Flask, render_template
# app = Flask(__name__)
#
# # Dummy example data
# devices = [
#     {"name": "Button 1", "actions": ["single", "double"], "events": ["battery_low"]},
#     {"name": "Sensor A", "actions": [], "events": ["motion", "temperature"]},
# ]
#
# @app.route("/")
# def index():
#     return render_template("index.html", devices=devices)
#
# # Run Flask in a separate thread
# def run_flask():
#     app.run(debug=False, use_reloader=False)


async def main():
    # flask_thread = threading.Thread(target=run_flask)
    # flask_thread.start()
    await client.start()

asyncio.run(main())