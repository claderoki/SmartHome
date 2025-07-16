from api import Client, MqttObject, event

import os
import platform
import asyncio

class Desktop(MqttObject):
    @event(lambda x: x == 'shutdown')
    async def on_shutdown(self, _):
        if platform.system() == "Linux":
            os.system("shutdown now")
        elif platform.system() == "Windows":
            os.system("shutdown /s /t 0")


client = Client("192.168.2.11")

_ = client.add_device(Desktop('computer/desktop 1'))

async def main():
    await client.start()

asyncio.run(main())