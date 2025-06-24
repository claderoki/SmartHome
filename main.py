from api import Client, Switch, Bulb, event, Doorbell


class DefaultDoorbell(Doorbell):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb

    @event()
    def on_ring(self, payload):
        self.bulb.toggle()


class DefaultSwitch(Switch):
    def __init__(self, name, bulb: Bulb):
        super().__init__(name)
        self.bulb = bulb
        self._steps = 20

    @event()
    def on_press(self, payload):
        if self.bulb.is_on():
            self.bulb.set_brightness(self.bulb.BRIGHTNESS_MAX)
        else:
            self.bulb.set_on()

    @event()
    def off_press(self, payload):
        self.bulb.set_off()

    @event()
    def down_press(self, payload):
        self.bulb.decrease_brightness(self._steps)

    @event()
    def up_press(self, payload):
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

client.start()
