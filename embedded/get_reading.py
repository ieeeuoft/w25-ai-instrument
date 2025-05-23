import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

def get_reading():

	# create the spi bus
	spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

	# create the cs (chip select)
	cs = digitalio.DigitalInOut(board.D5)

	# create the mcp object
	mcp = MCP.MCP3008(spi, cs)

	# create an analog input channel on pin 0
	chan = AnalogIn(mcp, MCP.P0)
	chan2 = AnalogIn(mcp, MCP.P1)

	# print('Raw ADC Value: ', chan.value)
	# print('ADC Voltage: ' + str(chan.voltage) + 'V')
	return [chan.voltage, chan2.voltage]
	
if __name__ == "__main__":
	print(get_reading())
