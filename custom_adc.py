import RPi.GPIO as GPIO
import smbus
import time

class Adc():
    def __init__(self, bus, pin, dac):
        self.I2C_DATA_ADDR = 0x20
        self.I2C_ENABLED_ADDR = 0x3c
        self.DAC_EN = [0xBF, 0x7F]

        self.bus = bus
        self.dac = dac
        self.COMP_PIN = pin

        try:
            self.bus.write_byte (self.I2C_DATA_ADDR, 0)   # This supposedly clears the port
        except IOError:
            print ("Comms err")

        try:
            self.bus.write_byte (self.I2C_ENABLED_ADDR, 255)  # This is meant to clear the other port
        except IOError:
            print ("Comms err")



        GPIO.setwarnings (False) # This is the usaul GPIO jazz
        GPIO.setmode (GPIO.BCM)
        GPIO.setup (self.COMP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def update (self, value):
        try:
            self.bus.write_byte (self.I2C_DATA_ADDR, value)
            self.bus.write_byte (self.I2C_ENABLED_ADDR, self.DAC_EN[self.dac])
            self.bus.write_byte (self.I2C_ENABLED_ADDR, 255)  # Clear port after sending data
        except IOError:
            print ("Another Comms err")

    def get_comp (self):
        return GPIO.input (self.COMP_PIN)

    def approx (self):
        count = 0
        new = 0
        self.update (0)

        for i in range (0, 8):
            new = count | 2 ** (7 - i) # Performs bitwise OR to go from top down if needed

            self.update (new)
            if self.get_comp () == False:
                count = new

        return count

    def ramp (self):
        count = 0
        self.update (0)

        for i in range (0,255):
            #if self.get_comp() == False:
            if True:
                print ("Count has called")
                count += 1
                self.update (i)
            else:
                break
        return count


def main ():
    bus = smbus.SMBus (1)
    time.sleep (1)
    adc = Adc (bus, 25, 1)

    while True:
        #value = adc.approx ()
        value = adc.ramp()

        if value > 160:
            print (value)

        time.sleep (0.001)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    #finally:








