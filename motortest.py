import time
import stepper
import readline  # This enables command history

def main():
    try:
        while True:
            # Read input with history support
            command_input = input("> ")

            # Split the input into parts
            parts = command_input.split()

            if parts[0].startswith('m') and len(parts) == 3:
                motor = parts[0]
                steps = int(parts[1])
                speed = float(parts[2])

                if motor == "m1":
                    stepper.m1_move(steps, speed, True)
                elif motor == "m2":
                    stepper.m2_move(steps, speed, False)
                else:
                    print("Unknown motor command")
            else:
                print("Invalid command format. Use: m1 <steps> <speed> or m2 <steps> <speed>. Speed 0-9.")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stepper.cleanup()


if __name__ == "__main__":
    main()
