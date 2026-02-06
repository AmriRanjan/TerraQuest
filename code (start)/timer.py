from pygame.time import get_ticks # let us get the current time in milliseconds

class Timer:
	def __init__(self, duration, repeat = False, autostart = False, func = None):

		# Initialise Timer object with these named parameters and attributes:
		self.duration = duration # length of time in milliseconds before timer triggers
		self.start_time = 0
		self.active = False
		self.repeat = repeat # can be True or False. If True, timer automatically restarts after finishing 
		self.func = func
		if autostart: # set initially to False, but if True, then timer starts immediately upon being made
			self.start()

	def start(self):
		self.active = True # indicate timer running
		self.start_time = get_ticks() # record the current pygame time in milliseconds

	def stop(self):
		self.active = False # indicate timer inactive
		self.start_time = 0 # reset start time to erase the current pygame time that was stored in it
		if self.repeat: # if wanting to restart, then run start() method again
			self.start()

	def update(self): 
		if self.active: # whenever timer is active
			current_time = get_ticks()
			if current_time - self.start_time >= self.duration: # if elapsed time has surpassed or reached duration intended for it
				if self.func: 
					self.func()
				self.stop() # close timer

