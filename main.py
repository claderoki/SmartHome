from api import Context, Switch, Bulb


class DefaultSwitch(Switch):
    def __init__(self, context, name, bulb: Bulb):
        super().__init__(context, name)
        self.bulb = bulb
        self._steps = 20

    def on_press(self, payload):
        if self.bulb.is_on():
            self.bulb.set_brightness(self.bulb.BRIGHTNESS_MAX)
        else:
            self.bulb.set_on()

    def off_press(self, payload):
        self.bulb.set_off()

    def down_press(self, payload):
        self.bulb.decrease_brightness(self._steps)

    def up_press(self, payload):
        self.bulb.increase_brightness(self._steps)

context = Context("192.168.2.11")

bulb1 = context.add_device(Bulb(context, 'zigbee2mqtt/Bulb 1'))
bulb2 = context.add_device(Bulb(context, 'zigbee2mqtt/Bulb 2'))
bulb3 = context.add_device(Bulb(context, 'zigbee2mqtt/Bulb 3'))

switch1 = context.add_device(DefaultSwitch(context, 'zigbee2mqtt/Switch 1', bulb1))
switch2 = context.add_device(DefaultSwitch(context, 'zigbee2mqtt/Switch 2', bulb2))
switch3 = context.add_device(DefaultSwitch(context, 'zigbee2mqtt/Switch 3', bulb3))

context.start()
