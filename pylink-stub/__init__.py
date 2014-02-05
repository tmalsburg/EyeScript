import pygame
TRIAL_OK = 0
REPEAT_TRIAL = 1
SKIP_TRIAL = 2
ABORT_EXPT = 3
KB_BUTTON = 65000
KB_PRESS = 10
KB_RELEASE = -1
pygame.init()
def beginRealTimeMode(delay):
    pygame.time.delay(delay)
def msecDelay(ticks):
    pygame.time.delay(ticks)
def currentTime():
    return pygame.time.get_ticks()
def openGraphicsEx(*args,**kw):
    pass
def setDriftCorrectSounds(*args,**kw):
    pass
def endRealTimeMode(*args,**kw):
    pass
class EyeLinkCustomDisplay:
	def __init__(self):
		pass
	def setup_cal_display     (self): pass
	def exit_cal_display      (self): pass
	def record_abort_hide     (self): pass
	def setup_image_display   (self, width, height): pass
	def image_title           (self, threshold, cam_name): pass
	def draw_image_line       (self, width, line, totlines,buff): pass
	def set_image_palette     (self, red, green, blue): pass
	def exit_image_display    (self): pass
	def clear_cal_display     (self): pass
	def erase_cal_target      (self): pass
	def draw_cal_target       (self, x, y): pass
	def cal_target_beep       (self): pass
	def cal_done_beep         (self,error) : pass
	def dc_done_beep          (self,error) : pass
	def dc_target_beep        (self) : pass
	def get_input_key         (self): pass
	def alert_printf          (self,msg): pass
