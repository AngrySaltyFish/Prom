# ADC TEST CODE
# TEST 1: to check if the ADC's I2C interface is working, at 
# the command line type : sudo i2cdetect -y 1 
# This will scan the I2C bus, returning active addresses. If 
# the ADC is work address 0x21 will be listed. 
# First words of advice : ** READ THE ADC's DATA SHEET ** 
# When you have done this consider the Python code below. 
# I would suggest using the ADC in mode 2. A description is 
# on page 29. To read an input you must first write a command 
# word to the ADC, triggering the conversion. Then the 
# converted value can be read back. HOWEVER, the 16 bit value 
# read back contains additional information, as described on 
# page 20.
import smbus
import time
I2CADDR = 0x21 
CMD_CODE = 0b01000000
# identify this from the data sheet
bus = smbus.SMBus(1)
bus.write_byte( I2CADDR, CMD_CODE )
tmp = bin(bus.read_word_data( I2CADDR, 0x00 ))


value = tmp[10:] + tmp[2:10]

print (int(value))
