import os
import sys
import time
import random
from serial import Serial

#so that testing can be done on windows:
#from colorama import init
#init()


"""
Plan:

GameState class:
initialize game state, height, width, refresh speed, colours..

Ball class:
moves the ball/ controls the properties of the ball, e.g. speed, coords
ball will be only object checking for collisions. Check for collision every step

Player class:
controls the bat properties
size, current coords

"""

serPort = Serial("/dev/ttyAMA0", 9600)

if(serPort.isOpen() == False):
	serPort.open()



#Constants:

const_room_width = 80
const_room_height = 24
const_net_x = 40
const_update_speed = 0.05
const_back_col = str(chr(27)) + "[47m"
const_net_col = str(chr(27)) + "[44m"
const_ball_col = str(chr(27)) + "[41m"
const_bat_col = str(chr(27)) + "[40m"
const_number_col = str(chr(27)) + "[45m"

const_bat_offset = 4
const_score_offset = 8
####

# Open Pi serial port, speed 9600 bits per second
#erialPort = Serial("/dev/ttyAMA0", 9600)
# Should not need, but just in case
#if (serialPort.isOpen() == False):
#	serialPort.open()


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

		#test#
		sys.stdout.write(str(chr(27)) + "[=14h")

		#Create a dictionary that will hold any positional changes of the objects, e.g. the bats or ball
		self._change = {}

		self._change["Ball"] = []
		self._change["Net"] = []
		self._change["Score"] = [1, 0]
		#_change[1] and _change[2] will be the two different player IDs
		self._change[1] = []
		self._change[2] = []

		####Initially create game display:####
		####DRAW SCORE####
		self.update_score(1, 0)
		self.update_score(2, 0)

		#Draw background:
		for i in range(self._height):
			for j in range(self._width):
				sys.stdout.write(self._backCol + " ")
			print(str(chr(27)) + "[0m")	#Prints new line

		#Draw net:
		count = -1
		switch = 0
		for i in range(self._height+1):
			#Set net colour on every other twos
			if(switch):
				self.write(i, self._netX, self._netCol)

			count+=1
			if(count > 1):
				count = 0
				switch ^= 1

	def write_change(self, ID, arr):
		self._change[ID] = arr

	#This function moves the cursor to position and then writes the desired colour
	def write(self, x, y, col):
		if(x<0): x=0
		if(x>self._height): x=self._height

		string = str(chr(27)) + "["+str(x)+";"+str(y)+"H" + col + " "
		self._buffer += string

		sys.stdout.write(string)
		#sys.stdout.write(col + " ")
		sys.stdout.flush()

	def update_net(self):
		#Could be optimised!!

		#Draw net:
		count = -1
		switch = 0
		for i in range(self._height+1):
			#Set net colour on every other twos
			if(switch):
				self.write(i, self._netX, self._netCol)

			count+=1
			if(count > 1):
				count = 0
				switch ^= 1

	#def update_bat(self, ID, newY, prevY, batSize):

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
				x=2
				y += 1
				for val in line:
					x-=1
					if(int(val)):
						self.write(y, self._netX + const_score_offset - x + 2, self._numCol)
					else:
						self.write(y, self._netX + const_score_offset - x + 2, self._backCol)

		#else:


	def update_image(self):
		#Sleep for update speed:
		time.sleep(self._updateSpeed)

		self._buffer = ""

		#Update sequence is least important(lowest depth) to most, e.g. net first then ball, this way
		#the ball will be drawn over the net.

		####Update net####
		arr = self._change["Net"]
		if(arr):
			self.update_net()
			self._change["Net"] = []
		####

		####UPDATE SCORE####
		arr = self._change["Score"]

		if(arr):
			self.update_score(arr[0], arr[1])
			self._change["score"] = []

		####Update ball####
		#Create a temporary array:
		arr = self._change["Ball"]

		#If the array is not empty, then
		if(arr):
			#Move cursor to new coords:
			self.write(arr[0], arr[1], self._ballCol)
			#Move cursor to old coords:
			self.write(arr[2], arr[3], self._backCol)

			#Reset the ball changes:
			self._change["Ball"] = []
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

		####
		serPort.write(self._buffer)

class Ball:
	def __init__(self, xspeed, yspeed, x, y, update_speed):
		self._xspeed = xspeed
		self._yspeed = yspeed
		self._x = x
		self._y = y

		#To control the ball speed, each step the ball will increment its update date count, once update count reaches
		#the desired update speed, the ball will be allowed to move 1 step.
		self._updateSpeed = update_speed
		#self._updateCount = 0

	def move(self, game, prevX, prevY):
		#self._updateCount += 1
		#if(self._updateCount==self._updateSpeed):
		#	self._updateCount = 0

		self._x += self._yspeed
		self._y += self._xspeed

		arr = [self._x, self._y, prevX, prevY]
		game.write_change("Ball", arr)

	def bounce(self, direction):
		if(direction=="v"):
			self._yspeed *= -1
		elif(direction=="h"):
			self._xspeed *= -1

	def reset(self):
		self._x = 10
		self._y = 40

	def place_meeting(self, y, x, game, bat1, bat2):
		"""
		Possible collison points:
		The top and bottom wall: bounce
		the left and right wall: reset
		Either bat: change direction and bounce

		Intersecting the net
		"""
		#Wait for the bat to be allowed to update before doing collision checks:
		#if(self._updateCount > 0):
		#	return


		#Walls or bats:
		if(y == 1):
			self.bounce("v")
			return
		if(y == const_room_height):
			self.bounce("v")
			return
		if(x <= const_bat_offset+1):
			if(x == const_bat_offset+1 and (y<=bat1._y+bat1._size and y>=bat1._y)):
				self.bounce("h")
				return
			elif(x==1):
				self.reset()
				bat1.update_score()
				game.write_change("Score", [1, bat1._score])
				return
		elif(x >= const_room_width-const_bat_offset-1):
			if(x == const_room_width-const_bat_offset-1 and (y<=bat2._y+bat2._size and y>=bat2._y)):
				self.bounce("h")
				return
			elif(x == const_room_width-1):
				self.reset()
				bat2.update_score()
				game.write_change("Score", [2, bat2._score])
				return
		#Net:
		if(x == const_net_x-1 or x == const_net_x+1):
			game.write_change("Net", 1)


class Player:
	def __init__(self, ID, y, size, offset):
		self._ID = ID
		self._y = y
		self._size = size
		self._offset = offset

		self._score = 0

		#temp
		self.dir = 1

	def update_score(self):
		self._score += 1
		if(self._score>9):
			self._score = 0

	def move(self, inp_port, game):
		#direction = 1 #Will work out by the input from the controllers

		if(const_room_height+1 > self._y+self._size and self._y > 0):
			self._y+=self.dir
			#time.sleep(0.1)
			arr = [self._y, self.dir, self._size]
			game.write_change(self._ID, arr)
		else:
			self.dir *= -1
			self._y+=self.dir





ball = Ball(1, 1, 10, 40, 2)
bat1 = Player(1, 8, 8, const_bat_offset+1)
bat2 = Player(2, 8, 8, const_bat_offset+1)

game = GameState(const_room_height, const_room_width, const_net_x, const_update_speed, const_back_col, const_net_col, const_ball_col, const_bat_col, const_number_col)
while(True):
	prevX = ball._x
	prevY = ball._y
	ball.place_meeting(ball._x, ball._y, game, bat1, bat2)
	ball.move(game, prevX, prevY)

	bat1.move(8000, game)
	bat2.move(9000, game)

	game.update_image()

	#input_string = serialPort.read()
	#print "ASCII Value: " + str(ord(input_string))
	#serialPort.write(game._buffer)
	#time.sleep(0.1)

serPort.close()
