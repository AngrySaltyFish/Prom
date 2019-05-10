import os
import sys
import time
import random
import math
import RPi.GPIO as GPIO
import smbus
from serial import Serial
from Constants import *
####

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)

serialPort = Serial("/dev/ttyAMA0", 115200)

if (serialPort.isOpen() == False):
	serialPort.open()


class GameState:
	def __init__(self, room_height, room_width, net_x, update_speed, background_col, net_col, ball_col, bat_col, number_col):
		"""
		GameState(room_height, room_width, net_x, update_speed, background_col, net_col, ball_col, bat_col);
		http://ascii-table.com/ansi-escape-sequences.php
		"""
		self._height = room_height
		self._width = room_width
		self._netX = net_x
		self._updateSpeed = update_speed

		#Buffer for holding ansi escape sequences
		self._buffer = ""

		#Colours
		self._backCol = background_col
		self._netCol = net_col
		self._ballCol = ball_col
		self._batCol = bat_col
		self._numCol = number_col
		#
		#Number arrays
		self._numbers = {
			"0": ["111","101","101","101","111"],
			"1": ["010","110","010","010","111"],
			"2": ["111","001","111","100","111"],
			"3": ["111","001","111","001","111"],
			"4": ["101","101","111","001","001"],
			"5": ["111","100","111","001","111"],
			"6": ["111","100","111","101","111"],
			"7": ["111","001","010","100","100"],
			"8": ["111","101","111","101","111"],
			"9": ["111","101","111","001","001"]
		}


		#Create a dictionary that will hold any positional changes of the objects, e.g. the bats or ball
		self._change = {
			"Ball": [],
			"Net": [],
			"Score": [],
			1: [],
			2: []
		}

		####Initially create game display:####
		self._buffer += str(chr(27)) + "[2J" #Clear the console
		self._buffer += str(chr(27)) + "[?25l"

		#Draw background:
		for i in range(self._height+1):
			for j in range(self._width):
				self.write(i, j, self._backCol + " ")
			#sys.stdout.write(str(chr(27)) + "[0m")	#Prints new line
			self._buffer += str(chr(27)) + "[0m"



		####DRAW SCORE####
		self.update_score(1, 0)
		self.update_score(2, 0)

		##draw net
		for i in range(1, const_room_height+1):
			if(math.floor((i+1)/2) % 2 == 0):
				self.write(i, const_net_x, const_net_col)

	def write_change(self, ID, arr):
		self._change[ID] = arr

	#This function moves the cursor to position and then writes the desired colour
	def write(self, x, y, col):
		if(x<0): return
		if(x>self._height): return

		string = str(chr(27)) + "["+str(x)+";"+str(y)+"H" + col + " "
		self._buffer += string

		#sys.stdout.write(string)
		#sys.stdout.flush()

	def update_net(self, y):
		#Draw net:
		for i in range(1, const_room_height+1):
			if(math.floor((i+1)/2) % 2 == 0):
				self.write(i, const_net_x, const_net_col)
		#if(math.floor((y+1)/2) % 2 == 0):
		#	self.write(y, const_net_x, const_net_col)

	def update_score(self, ID, score):
		y=1
		x=0
		if (score > 9): score = 0

		if(ID == 1):
			#Draw number:
			num = self._numbers[str(score)]
			for line in num:
				x=0
				y += 1
				for val in line:
					x+=1
					if(int(val)):
						self.write(y, self._netX - const_score_offset -4  + x, self._numCol)
					else:
						self.write(y, self._netX - const_score_offset -4 + x , self._backCol)
		else:
			num = self._numbers[str(score)]
			for line in num:
				x=0
				y += 1
				for val in line:
					x+=1
					if(int(val)):
						self.write(y, self._netX + const_score_offset + x, self._numCol)
					else:
						self.write(y, self._netX + const_score_offset + x, self._backCol)


	def update_image(self, bat1Score, bat2Score):
		#Sleep for update speed:
		#time.sleep(self._updateSpeed)

		#Update sequence is least important(lowest depth) to most, e.g. net first then ball, this way
		#the ball will be drawn over the net.

		####UPDATE SCORE####
		arr = self._change["Score"]

		if(arr):
			self.update_score(arr[0], arr[1])
			self._change["Score"] = []

		####Update ball####
		#Create a temporary array:
		arr = self._change["Ball"]

		#If the array is not empty, then
		if(arr):
			x = arr[0]
			y = arr[1]
			px = arr[2]
			py = arr[3]

			#Move cursor to old coords:
			sOff1 = self._netX - const_score_offset - 4
			sOff2 = self._netX + const_score_offset

			if(px<7 and px>1):
				if(py > sOff1 and py < sOff1+4):
					#print(py - sOff1-1)
					if(self._numbers[str(bat1Score)][px-2][py - sOff1-1] == "1"):
						self.write(px,py, self._numCol)
					else:
						self.write(px, py, self._backCol)
				elif(py > sOff2 and py < sOff2+4):
					if(self._numbers[str(bat2Score)][px-2][py - sOff2-1] == "1"):
						self.write(px,py, self._numCol)
					else:
						self.write(px, py, self._backCol)
				else:
					self.write(px, py, self._backCol)
			else:
				self.write(px, py, self._backCol)
			#Reset the ball changes:

			#Move cursor to new coords:
			self.write(x, y, self._ballCol)

			self._change["Ball"] = []
		####

		####Update net####
		arr = self._change["Net"]
		if(arr):
			self.update_net(arr[0])
			self._change["Net"] = []
		####

		####Update bat1####
		arr = self._change[1]
		if(arr):
			y = int(arr[0])
			prevY = int(arr[1])
			size = arr[2]
			for i in range(const_room_height-prevY, const_room_height-prevY+size):
				self.write(i, const_bat_offset, self._backCol)
			for i in range(const_room_height-y, const_room_height-y+size):
				self.write(i, const_bat_offset, self._batCol)

			self._change[1] = []
		####
		####Update bat2####
		arr = self._change[2]
		if(arr):
			y = int(arr[0])
			prevY = int(arr[1])
			size = arr[2]
			for i in range(const_room_height-prevY, const_room_height-prevY+size):
				self.write(i, self._width-const_bat_offset, self._backCol)
			for i in range(const_room_height-y, const_room_height-y+size):
				self.write(i, self._width-const_bat_offset, self._batCol)

			self._change[2] = []
		####

class Ball:
	def __init__(self, xspeed, yspeed, x, y, update_speed):
		self._xspeed = xspeed
		self._yspeed = yspeed
		self._x = x
		self._y = y
		self._servingplayer = random.choice([1,2])
		self._serving = self._servingplayer
		#To control the ball speed, each step the ball will increment its update date count, once update count reaches
		#the desired update speed, the ball will be allowed to move 1 step.
		self._updateSpeed = update_speed
		self._updateCount = 0
		self._serves = 5

	def move(self, game, prevX, prevY):
		self._updateCount += 1
		if(self._updateCount>=self._updateSpeed and self._serving == 0):
			self._updateCount = 0

			self._x += self._yspeed
			self._y += self._xspeed

			arr = [self._x, self._y, prevX, prevY]
			game.write_change("Ball", arr)

	def bounce(self, xspd, yspd):
		self._yspeed = yspd
		self._xspeed = xspd

	def reset(self):
		prevX = self._x
		prevY = self._y
		self._x = 10
		self._y = 40
		self._updateSpeed = 2
		self._yspeed = random.choice([-1,1])

		arr = [self._x, self._y, prevX, prevY]
		game.write_change("Ball", arr)

	def get_x(self):
		return self._x
	def get_y(self):
		return self._y

	def set_xy(self,x, y):
		prevX = self._x
		self._x = x
		prevY = self._y
		self._y = y

		arr = [self._x, self._y, prevX, prevY]
		game.write_change("Ball", arr)

	def set_serving(self, val):
		self._serving = val

	def serve(self, bat):
		if(self._serving == 1):
			self.bounce(1, 0)
			self._serving = 0
		elif(self._serving == 2):
			self.bounce(-1, 0)
			self._serving = 0

	def place_meeting(self, y, x, game, bat1, bat2):
		"""
		Possible collison points:
		The top and bottom wall: bounce
		the left and right wall: reset
		Either bat: change direction and bounce

		Intersecting the net
		"""

		if(self._serving==1):
			if(bat1._prevY != bat1.get_y()):
				self.set_xy(const_room_height-bat1.get_y()+1, bat1.get_x())
			else:
				arr = [self._x, self._y, self._x, self._y]
				game.write_change("Ball", arr)

		elif(self._serving==2):
			#self.set_x(const_room_height-bat2.get_x()+1)
			if(bat2._prevY != bat2.get_y()):
				self.set_xy(const_room_height-bat2.get_y()+1, bat2.get_x())
			else:
				arr = [self._x, self._y, self._x, self._y]
				game.write_change("Ball", arr)

		#Wait for the bat to be allowed to update before doing collision checks:
		if(self._updateCount > 0):
			return
		#y = const_room_height-y
		#Walls or bats:

		bally = const_room_height-y

		if(bally == 0 or bally == const_room_height-1):
			self.bounce(self._xspeed, self._yspeed*-1)

		if(x <= const_bat_offset+1):
			if(x == const_bat_offset+1 and (bally>=bat1._y-bat1._size and bally<=bat1._y)):
				self._updateSpeed = random.randint(1,3)
				batYoffset = bat1._y-bally
				if(bat1._size==3):
					if(batYoffset == 0):
						self.bounce(self._xspeed*-1, -1)
					if(batYoffset == 1):
						self.bounce(self._xspeed*-1, 0)
					if(batYoffset == 2):
						self.bounce(self._xspeed*-1, 1)
					return
				if(bat1._size==6):
					if(batYoffset == 0 or batYoffset == 1):
						self.bounce(self._xspeed*-1, -1)
					if(batYoffset == 2 or batYoffset == 3):
						self.bounce(self._xspeed*-1, 0)
					if(batYoffset == 5 or batYoffset == 4):
						self.bounce(self._xspeed*-1, 1)
					return
			elif(x==1):
				self._serving = self._servingplayer
				self._serves -= 1
				if (self._serves == 0):
					if (self._servingplayer ==1): self._servingplayer=2
					elif (self._servingplayer ==2): self._servingplayer=1
					self._serves=5;

				bat2.update_score()
				game.write_change("Score", [2, bat2._score])
				return
		elif(x >= const_room_width-const_bat_offset-1):
			if(x == const_room_width-const_bat_offset-1 and (bally>=bat2._y-bat2._size and bally<=bat2._y)):
				self._updateSpeed = random.randint(1,3)

				batYoffset = bat2._y-bally
				if(bat2._size==3):
					if(batYoffset == 0):
						self.bounce(self._xspeed*-1, -1)
					if(batYoffset == 1):
						self.bounce(self._xspeed*-1, 0)
					if(batYoffset == 2):
						self.bounce(self._xspeed*-1, 1)
					return
				if(bat2._size==6):
					if(batYoffset == 0 or batYoffset == 1):
						self.bounce(self._xspeed*-1, -1)
					if(batYoffset == 2 or batYoffset == 3):
						self.bounce(self._xspeed*-1, 0)
					if(batYoffset == 4 or batYoffset == 5):
						self.bounce(self._xspeed*-1, 1)
					return
			elif(x == const_room_width-1):
				self._serving = self._servingplayer
				self._serves -= 1
				if (self._serves == 0):
					if (self._servingplayer ==1): self._servingplayer=2
					elif (self._servingplayer ==2): self._servingplayer=1
					self._serves=5

				bat1.update_score()
				game.write_change("Score", [1, bat1._score])
				return
		#Net:
		if(x == const_net_x):
			game.write_change("Net", [y])

	def get_relative_pos(self):
		return round(float(self.get_y()) / float(const_room_width)*8)


class Player:
	def __init__(self, ID, y, size, offset):
		self._ID = ID
		self._y = y
		self._size = size
		self._offset = offset
		self._prevY = y
		self._score = 0
		self._serves = 5

		if(ID == 1):
			self._x = offset
		else:
			self._x = const_room_width-offset
		#temp
		self.dir = 1
	def get_score(self):
		return self._score
	def get_y(self):
		return self._y
	def get_x(self):
		return self._x

	def update_score(self):
		self._score += 1

	def move(self, pos, prevY, game):
		#direction = 1 #Will work out by the input from the controllers
		self._prevY = self._y
		self._y = pos
		arr = [pos, prevY, self._size]
		game.write_change(self._ID, arr)

class Adc():
	def __init__(self, bus, pin):
		self.I2C_DATA_ADDR = 0x3c
		self.I2C_DATA_ADDR2 = 0x21
		self.bus = bus
		self.COMP_PIN = pin

		try:
			self.bus.write_byte (self.I2C_DATA_ADDR, 0) # This supposedly clears the port
			#self.bus.write_byte (self.I2C_DATA_ADDR2, 0)
		except IOError:
			print ("Comms err")
		GPIO.setwarnings (False) # This is the usaul GPIO jazz
		GPIO.setmode (GPIO.BCM)
		GPIO.setup (self.COMP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	def update (self, value):
		try:
			self.bus.write_byte (self.I2C_DATA_ADDR, value)
		except IOError:
			print ("Another Comms err")

	def get_comp (self):
        	return GPIO.input (self.COMP_PIN)

	def integrated (self):
		I2CADDR = 0x21
		CMD_CODE = 0b01000000
		bus = smbus.SMBus(1)
		bus.write_byte( I2CADDR, CMD_CODE )
		tmp = bus.read_word_data( I2CADDR, 0x00 )

		high_byte = (tmp&0b0000000011111111) << 8
		low_byte = tmp >> 8

		value = (high_byte + low_byte) & 0b0000111111111111
		return(value)

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

def LED_output(port, prev_port, bus):
	if(port<0):
		port = 0
	ports = {
		0: [5, 1],
		1: [6, 2],
		2: [12, 4],
		3: [13,8],
		4: [16, 16],
		5: [19, 32],
		6: [20, 64],
		7: [26, 128],
		8: [26, 128]
	}

	bus.write_byte (0x38, 255-ports[port][1])

	GPIO.setup(ports[port][0],GPIO.OUT)
	GPIO.output(ports[port][0],GPIO.HIGH)
	if(prev_port != None and prev_port != port):
		GPIO.output(ports[prev_port][0],GPIO.LOW)

def button_input(bus):
	i2cvalue = bus.read_byte(0x3e)
	b1 = i2cvalue & 0b00001000
	b2 = i2cvalue & 0b00000100
	b3 = i2cvalue & 0b00000010
	b4 = i2cvalue & 0b00000001

	return b1, b2, b3, b4

def diagnosticprint(rawbat1,rawbat2,current_pos_bat1,current_pos_bat2, bus, remainingtime1, remainingtime2): #button states, adc values, bat heights/states
	rem1_grow, rem1_serve, rem2_grow, rem2_serve = button_input(bus)
	print(chr(27) + "[2J")
	print("Ball X = " + str(ball._y) + ", Ball Y = " + str(const_room_height-ball._x) + ", Bat1: ADC: " + str(rawbat1) + " Y: " + str(current_pos_bat1) + " Sze: " + str(bat1._size) + ", Bat2: ADC: " + str(rawbat2) + " Y: " + str(current_pos_bat2) + " Sze: " + str(bat2._size))
	print("Growplayer1: " + str(rem1_grow) + ", ServePlayer1: " + str(rem1_serve) + ", GrowPlayer2: " + str(rem2_grow) + ", ServePlayer2: " + str(rem2_serve), ", Time Left Player 1: " + str(remainingtime1), ", Time Left Player 2: " + str(remainingtime2))


begin = time.time()
game = GameState(const_room_height, const_room_width, const_net_x, const_update_speed, const_back_col, const_net_col, const_ball_col, const_bat_col, const_number_col)
end = time.time()
print("Setup time: " + str(end-begin))

ball = Ball(-1, 1, 10, 40, 1)
bat1 = Player(1, 8, 3, const_bat_offset+1)
bat2 = Player(2, 8, 3, const_bat_offset+1)

def main ():
	bus = smbus.SMBus (1)
	time.sleep (1)
	adc = Adc (bus, 18)

	prev_pos_bat1 = 0
	prev_pos_bat2 = 01
	current_pos_bat1 = 0
	current_pos_bat2 = 0
	prev_port = None


	grows_player1 = 2
	grows_player2 = 2
	growtime1 = 0
	growtime2 = 0

	button_change_time = 0
	grow_button_change_time = 0
	prev_rem2_serve=0
	prev_rem2_grow=0

	remainingtime1=0
	remainingtime2=0
	while(True):
		if(bat1.get_score() > 9):
			print("Player 1 Wins!")
			break
		if(bat2.get_score() > 9):
			print("Player 2 Wins!")
			break

		rawbat1 = adc.approx() #value between 0-182
		rawbat2 = adc.integrated() #value between 0-3670
		time.sleep (0.02)

		#Moving the ball, checking for collisions
		prevX = ball.get_x()
		prevY = ball.get_y()
		ball.place_meeting(ball.get_x(), ball.get_y(), game, bat1, bat2)
		ball.move(game, prevX, prevY)

		#Get bat buttons
		bus.write_byte(0x3e, 0x00)
		rem1_grow, rem1_serve, rem2_grow, rem2_serve = button_input(bus)

		if(rem1_serve and ball._serving == 1):
			ball.serve(bat1)

		if(rem1_grow and grows_player1 > 0 and bat1._size==3):
			bat1._size=6
			grows_player1 -= 1
			growtime1 = time.time()

			arr = [bat1._y, bat1._y, bat1._size]
			game.write_change(bat1._ID, arr)

		#debouncing code
		if(rem2_serve!=prev_rem2_serve):
			button_change_time += 1
			if (button_change_time == 5):
				if(rem2_serve!=0):
					if(ball._serving == 2):
						ball.serve(bat2)
				prev_rem2_serve=rem2_serve
		if(rem2_serve==prev_rem2_serve):
			button_change_time=0

		if(rem2_grow!=prev_rem2_grow):
			grow_button_change_time += 1
			if (grow_button_change_time == 5):
				if (rem2_grow and grows_player2 > 0 and bat2._size==3):
					bat2._size=6
					grows_player2 -= 1
					growtime2 = time.time()
					arr = [bat2._y, bat2._y, bat2._size]
					game.write_change(bat2._ID, arr)
				prev_rem2_grow=rem2_grow
		if(rem2_grow==prev_rem2_grow):
			grow_button_change_time=0

		if(bat1._size==6):remainingtime1 = 15-(time.time()-growtime1)
		if(bat2._size==6):remainingtime2 = 15-(time.time()-growtime2)

		if(bat1._size == 6 and time.time()-growtime1 >= 15):
			bat1._size = 3
			arr = [bat1._y, bat1._y, bat1._size]
			game.write_change(bat1._ID, arr)

		if(bat2._size == 6 and time.time()-growtime2 >= 15):
			bat2._size = 3
			arr = [bat2._y, bat2._y, bat2._size]
			game.write_change(bat2._ID, arr)

		#0-21
		max_custom_adc=const_adc_max1
		prev_pos_bat1 = current_pos_bat1
		current_pos_bat1=int((float(rawbat1)/float(max_custom_adc))*22 + 2)

		#print(rawbat2)
		max_integrated=const_adc_max2
		prev_pos_bat2 = current_pos_bat2
		current_pos_bat2=int((float(rawbat2)/float(max_integrated))*22 + 2)

		#Move each bat individually
		if(current_pos_bat1 != prev_pos_bat1):
			bat1.move(current_pos_bat1, bat1.get_y(), game)
		if(current_pos_bat2 != prev_pos_bat2):
			bat2.move(current_pos_bat2, bat2.get_y(), game)

		#Update the game image. Feeding both bats scores into the function so that correct score can be written
		game.update_image(bat1.get_score(), bat2.get_score())

		#LED output
		LED_output(ball.get_relative_pos(), prev_port, bus)
		prev_port = ball.get_relative_pos()

		serialPort.write(game._buffer.encode("ascii"))
		game._buffer = ""
		#time.sleep(0.1)

		diagnosticprint(rawbat1, rawbat2, current_pos_bat1, current_pos_bat2, bus, remainingtime1, remainingtime2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

serialPort.close()
