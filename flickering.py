from api import Client, MqttObject, event, IkeaBulb, action, Flicker

import os
import platform
import asyncio

from extra import Button

client = Client("192.168.2.11")


class Button2(MqttObject):
    def __init__(self, name, *bulbs):
        super().__init__(name)
        self.bulbs = bulbs
        # for bulb in self.bulbs:
        #     bulb.set_brightness(75)

    @action()
    async def single(self, payload):
        tasks = [x.animate_toggle(Flicker()) for x in self.bulbs]
        all_groups = asyncio.gather(*tasks)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(all_groups)
        loop.close()

"""
Small bedroom light
Closet light
"""
bulb1 = client.add_device(IkeaBulb('zigbee2mqtt/Small bedroom light'))
bulb2 = client.add_device(IkeaBulb('zigbee2mqtt/Closet light'))
button2 = client.add_device(Button2('zigbee2mqtt/Button 2', bulb2, bulb1))

async def main():
    await client.start()

asyncio.run(main())