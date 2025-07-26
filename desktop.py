from api import Client, MqttObject, event

import os
import platform
import asyncio


class Desktop(MqttObject):
    def set_status(self, status):
        self.context.client.publish(f'{self.name}/status', status)

    @event(lambda x: x == 'OFF')
    async def on_shutdown(self, _):
        self.set_status('OFF')
        if platform.system() == "Linux":
            os.system("shutdown now")
        elif platform.system() == "Windows":
            os.system("shutdown /s /t 0")

    async def on_subscribe(self):
        self.set_status('ON')


client = Client("192.168.2.11")

_ = client.add_device(Desktop('computer/desktop 1'))

async def main():
    await client.start()

asyncio.run(main())