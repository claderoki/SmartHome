from api import  Switch, Bulb, action, Doorbell, MqttObject, Flicker, event

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

