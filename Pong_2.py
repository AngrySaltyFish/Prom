import os
import sys
import time
import random
import math
import RPi.GPIO as GPIO
import smbus
from serial import Serial

#Constants:

const_room_width = 80
const_room_height = 24
const_net_x = 40
const_update_speed = 0.04
const_back_col = str(chr(27)) + "[47m"
const_net_col = str(chr(27)) + "[44m"
const_ball_col = str(chr(27)) + "[41m"
const_bat_col = str(chr(27)) + "[40m"
const_number_col = str(chr(27)) + "[45m"

const_bat_offset = 4
const_score_offset = 8
####

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

serialPort = Serial("/dev/ttyAMA0", 9600)

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

		#Coordinate System#
		self._display = [[0 for i in range(room_height)] for j in range(room_width)]
		self._displayVals = {
			0: self._backCol,
			1: self._netCol,
			2: self._ballCol,
			3: self._batCol,
			4: self._numCol
		}
		self._displayCols = {
			self._backCol: 0,
			self._netCol: 1,
			self._ballCol: 2,
			self._batCol: 3,
			self._numCol: 4
		}

		#Create a dictionary that will hold any positional changes of the objects, e.g. the bats or ball
		self._change = {
			"Ball": [],
			"Net": [],
			"Score": [],
			"Player1": [],
			"Player2": []
		}

		####Initially create game display:####
		sys.stdout.write(chr(27) + "[2J")
		#Draw background:
		for i in range(self._height+1):
			for j in range(self._width):
				self.write(i, j, self._backCol + " ")
			sys.stdout.write(str(chr(27)) + "[0m")	#Prints new line
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

		sys.stdout.write(string)
		sys.stdout.flush()

	def update_net(self, y):
		#Draw net:
		if(math.floor((y+1)/2) % 2 == 0):
			self.write(y+1, const_net_x, const_net_col)

	def update_score(self, ID, score):
		y=1
		x=0

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
		time.sleep(self._updateSpeed)

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

			#Move cursor to new coords:
			self.write(x, y, self._ballCol)
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
			y = arr[0]
			direction = arr[1]
			size = arr[2]

			for i in range(size):
				self.write(y+i-direction, const_bat_offset, self._batCol)

			self.write(y-1, const_bat_offset, self._backCol)
			self.write(y+size, const_bat_offset, self._backCol)

			self._change[1] = []
		####
		####Update bat2####
		arr = self._change[2]
		if(arr):
			y = arr[0]
			direction = arr[1]
			size = arr[2]

			for i in range(size):
				self.write(y+i-direction, self._width-const_bat_offset, self._batCol)

			self.write(y-1, self._width-const_bat_offset, self._backCol)
			self.write(y+size, self._width-const_bat_offset, self._backCol)

			self._change[2] = []

class Ball:
	def __init__(self, xspeed, yspeed, x, y, update_speed):
		self._xspeed = xspeed
		self._yspeed = yspeed
		self._x = x
		self._y = y

		self._serving = 0
		#To control the ball speed, each step the ball will increment its update date count, once update count reaches
		#the desired update speed, the ball will be allowed to move 1 step.
		self._updateSpeed = update_speed
		self._updateCount = 0

	def move(self, game, prevX, prevY):
		self._updateCount += 1
		if(self._updateCount>=self._updateSpeed and self._serving == 0):
			self._updateCount = 0

			self._x += self._yspeed
			self._y += self._xspeed

			arr = [self._x, self._y, prevX, prevY]
			game.write_change("Ball", arr)

	def bounce(self, direction):
		self._updateSpeed = random.randint(1,10)

		if(direction=="v"):
			self._yspeed *= -1
		elif(direction=="h"):
			self._xspeed *= -1

	def reset(self):
		self._x = 10
		self._y = 40

	def get_x(self):
		return self._x
	def get_y(self):
		return self._y

	def set_x(self,x):
		self._x = x
	def set_y(self,y):
		self._y = y
	def set_serving(self, val):
		self._serving = val

	def place_meeting(self, y, x, game, bat1, bat2):
		"""
		Possible collison points:
		The top and bottom wall: bounce
		the left and right wall: reset
		Either bat: change direction and bounce

		Intersecting the net
		"""
		#Wait for the bat to be allowed to update before doing collision checks:
		if(self._updateCount > 0):
			return

		if(self._serving>0):
			if(self._serving == 1):
				self.set_x(bat1.get_x())
				self.set_y(bat1.get_y()+1)
			else:
				self.set_x(bat2.get_x())
				self.set_y(bat2.get_y()-1)
		else:
			#Walls or bats:
			if(y == 1):
				self.bounce("v")
			if(y == const_room_height):
				self.bounce("v")
			if(x <= const_bat_offset+1):
				if(x == const_bat_offset+1 and (y<=bat1._y+bat1._size and y>=bat1._y)):
					self.bounce("h")
					return
				elif(x==1):
					self._serving = 1

					bat2.update_score()
					game.write_change("Score", [2, bat2._score])
					return
			elif(x >= const_room_width-const_bat_offset-1):
				if(x == const_room_width-const_bat_offset-1 and (y<=bat2._y+bat2._size and y>=bat2._y)):
					self.bounce("h")
					return
				elif(x == const_room_width-1):
					self._serving = 2

					bat1.update_score()
					game.write_change("Score", [1, bat1._score])
					return
			#Net:
			if(x == const_net_x-1 or x == const_net_x+1):
				game.write_change("Net", [y])

	def get_relative_pos(self):
		return round(float(self._y) / float(const_room_width)*8)


class Player:
	def __init__(self, ID, y, size, offset):
		self._ID = ID
		self._y = y
		self._size = size
		self._offset = offset

		self._score = 0
		if(ID == 1):
			self._x = const_bat_offset
		else:
			self._x = const_room_width-const_bat_offset

		#temp
		self.dir = 1
	def get_score(self):
		return self._score
	def get_x(self):
		return self._x
	def get_y(self):
		return self._y

	def update_score(self):
		self._score += 1
		if(self._score>9):
			self._score = 0

	def move(self, inp_port, game):
		#direction = 1 #Will work out by the input from the controllers
		if(const_room_height+2 > self._y+self._size and self._y >= 0):
			self._y+=self.dir
			#time.sleep(0.1)
			arr = [self._y, self.dir, self._size]
			game.write_change(self._ID, arr)
		else:
			self.dir *= -1
			self._y+=self.dir

class Adc():
    def __init__(self, bus, pin):
        self.I2C_DATA_ADDR = 0x3c
        self.bus = bus
        self.COMP_PIN = pin

        try:
            self.bus.write_byte (self.I2C_DATA_ADDR, 0)   # This supposedly clears the port
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


def LED_output(port):
	ports = {
		0: 7,
		1: 7,
		2: 12,
		3: 12,
		4: 13,
		5: 16,
		6: 19,
		7: 19,
		8: 26
	}
	GPIO.setup(ports[port],GPIO.OUT)
	GPIO.output(ports[port],GPIO.HIGH)
	time.sleep(0.1)
	GPIO.output(ports[port],GPIO.LOW)

ball = Ball(-1, 1, 10, 40, 1)
bat1 = Player(1, 8, 4, const_bat_offset+1)
bat2 = Player(2, 8, 4, const_bat_offset+1)

game = GameState(const_room_height, const_room_width, const_net_x, const_update_speed, const_back_col, const_net_col, const_ball_col, const_bat_col, const_number_col)

def main ():
	bus = smbus.SMBus (1)
	time.sleep (1)
	adc = Adc (bus, 18)

	while(True):
		value = adc.approx()
		print (value)

		if value > 160:
			print (value)

		time.sleep (0.001)

		#Moving the ball, checking for collisions
		prevX = ball.get_x()
		prevY = ball.get_y()
		ball.place_meeting(ball.get_x(), ball.get_y(), game, bat1, bat2)
		ball.move(game, prevX, prevY)

		#if(something):
		#ball.

		#Move each bat individually
		bat1.move(8000, game)
		bat2.move(9000, game)

		#Update the game image. Feeding both bats scores into the function so that correct score can be written
		game.update_image(bat1.get_score(), bat2.get_score())

		#LED output
		LED_output(ball.get_relative_pos())

		serialPort.write(game._buffer.encode("ascii"))
		game._buffer = ""
		#time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

serialPort.close()
