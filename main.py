import time
from HR8825 import HR8825

Motor1 = HR8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
Motor2 = HR8825(dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))


def set_motor1_angle(steps, speed):
    # stepdelay = (9 - speed) * 0.001

    Motor1.SetMicroStep('softward', 'fullstep')
    Motor1.TurnStep(Dir='forward', steps=steps, stepdelay=speed)


def set_motor2_angle(steps, speed):
    Motor2.SetMicroStep('softward', 'fullstep')
    Motor2.TurnStep(Dir='forward', steps=steps, stepdelay=speed)


if __name__ == "__main__":
    while True:
        command_input = input(">")

        parts = command_input.split()

        if parts[0].startswith('m') and len(parts) == 3:
            if len(parts) == 3:
                motor = parts[0]
                steps = int(parts[1])
                speed = float(parts[2])
                # if speed > 9:
                #     speed = 9
                #
                # if speed < 0:
                #     speed = 0


                if motor == "m1":
                    set_motor1_angle(steps, speed)
                elif motor == "m2":
                    set_motor2_angle(steps, speed)
                else:
                    print("Unknown motor command")
            else:
                print("Invalid command format. Use: m1 <steps> <speed> or m2 <steps> <speed>. Speed 0-9.")
