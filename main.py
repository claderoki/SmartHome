import asyncio

from api import Client, Bulb, IkeaBulb, MqttObject
from extra import DefaultSwitch, Socket, ButtonLink, Button, SocketButton, StaticDetector

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

socket1 = client.add_device(Socket('zigbee2mqtt/Socket 1'))

button1 = client.add_device(ButtonLink('zigbee2mqtt/Button 1', tiny1, 'toggle'))
button2 = client.add_device(Button('zigbee2mqtt/Button 2'))
button3 = client.add_device(SocketButton('zigbee2mqtt/Button 3', socket1))

a = client.add_device(StaticDetector('zigbee2mqtt/Static 1', bulb3))
b = client.add_device(MqttObject('zigbee2mqtt/Door 1'))


async def main():
    await client.start()

asyncio.run(main())