#
# Copyright (c) 1996-2005, SR Research Ltd., All Rights Reserved
#
#
# For use by SR Research licencees only. Redistribution and use in source
# and binary forms, with or without modification, are NOT permitted.
#
#
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in
# the documentation and/or other materials provided with the distribution.
#
# Neither name of SR Research Ltd nor the name of contributors may be used
# to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS
# IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# $Date: 2005/11/01 14:12:02 $
# 
#


import pylink

from pygame import *
import time

import sys

from pygame import mixer
import pygame.event
from pygame.constants import *
import array
import pygame.image
from PIL import Image
import PIL.ImageDraw
import pygame.draw

sys.argv="EB Session","EB Session"
from VisionEgg import *
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
from VisionEgg.Core import *
from VisionEgg.MoreStimuli import *
from VisionEgg.Text import *
from VisionEgg.Textures import *
from os.path import join,isdir

for searchpath in sys.path:
    PATH = join(searchpath,'pylink','EyeLinkCoreGraphics')
    if isdir(PATH): break



#KB_PRESS=10
#KB_RELEASE=-1
#KB_REPEAT=1
#KB_BUTTON=0xFF00
#F1_KEY=0x3B00
#F2_KEY=0x3C00
#F3_KEY=0x3D00
#F4_KEY=0x3E00
#F5_KEY=0x3F00
#F6_KEY=0x4000
#F7_KEY=0x4100
#F8_KEY=0x4200
#F9_KEY=0x4300
#F10_KEY=0x4400
#PAGE_UP=0x4900
#PAGE_DOWN=0x5100
#CURS_UP=0x4800
#CURS_DOWN=0x5000
#CURS_LEFT=0x4B00
#CURS_RIGHT=0x4D00
#ESC_KEY=0x001B
#ENTER_KEY=0x000D
#JUNK_KEY=1

class KeyInput:
	def __init__(self,key,state=0):
		self.__key__ = key
		self.__state__ =state
		self.__type__= 0x1

def vline(idraw,x,y0,y1,col):
	idraw.line([(x,y0),(x,y1)], fill=col)
	
def hline(idraw,x0,x1,y,col):
	idraw.line([(x0,y),(x1,y)], fill=col)


class EyeLinkCoreGraphicsVE(pylink.EyeLinkCustomDisplay):
	def __init__(self,screen,tracker):
		self.size=screen.size
		self.tracker=tracker
		pylink.EyeLinkCustomDisplay.__init__(self)
		#display.init()
		pygame.mixer.init()
		#display.set_mode((1280, 1024), FULLSCREEN |DOUBLEBUF |RLEACCEL |DOUBLEBUF ,16)
		#self.__target_beep__ = pygame.mixer.Sound(join(PATH,"caltargetbeep.wav"))
		#self.__target_beep__done__ = pygame.mixer.Sound(join(PATH,"caltargetbeep.wav"))
		#self.__target_beep__error__ = pygame.mixer.Sound(join(PATH,"caltargetbeep.wav"))
		self.imagebuffer = array.array('l')
		self.pal = None	

		# Create viewport for calibration / DC 
		
		cal_screen = screen
		cal_screen.parameters.bgcolor = (1.0,1.0,1.0,1.0)

		innertarget = FilledCircle(radius = 2,anchor='center',color=(0,0,0),num_triangles=201)
		outertarget = FilledCircle(radius = 7,anchor='center',color=(1,1,1),num_triangles=401)

##		target = Target2D(size  = (10.0,10.0),
##                  		color      = (0.0,0.0,0.0,1.0), # Set the target color (RGBA) black
##                  		orientation = 0.0)

		self.cal_vp = Viewport(screen=cal_screen, stimuli=[outertarget,innertarget])		

		# Create viewport for camera image screen 
		text = Text(text="Eye Label",
            		color=(0.0,0.0,0.0), # alpha is ignored (set with max_alpha_param)
            		position=(cal_screen.size[0]/2,int(screen.size[1]*0.1)),
            		font_size=50,
            		anchor='center')

                     
		img =Image.new("RGBX",(int(screen.size[0]*0.75),int(screen.size[1]*0.75)))
		image = TextureStimulus(mipmaps_enabled=0,
			   texture=Texture(img),
			   size=(int(screen.size[0]*0.75),int(screen.size[1]*0.75)),
			   texture_min_filter=gl.GL_LINEAR,
			   position=(cal_screen.size[0]/2.0,cal_screen.size[1]/2.0),
			   anchor='center')

		#image = TextureStimulus(mipmaps_enabled=0,
		#	   texture=None,
		#	   size=(640,480),
		#	   texture_min_filter=gl.GL_LINEAR,
		#	   position=(cal_screen.size[0]/2.0,cal_screen.size[1]/2.0),
		#	   anchor='center')

		self.image_vp = Viewport(screen=cal_screen, stimuli=[text,image])		
		
		self.width=cal_screen.size[0]
		self.height=cal_screen.size[1]
		
		
	def setup_cal_display (self):
		self.cal_vp.parameters.screen.clear()
		VisionEgg.Core.swap_buffers()

	def setCalibrationColors(self, foreground_color, background_color):
            self.cal_vp.parameters.screen.parameters.bgcolor = background_color
            self.cal_vp.parameters.stimuli[0].parameters.color = foreground_color
            self.cal_vp.parameters.stimuli[1].parameters.color = background_color
				
	def exit_cal_display(self): 
		self.clear_cal_display()
		
	def record_abort_hide(self):
		pass

	def clear_cal_display(self): 
		self.cal_vp.parameters.screen.clear()
		VisionEgg.Core.swap_buffers()
		
	def erase_cal_target(self):
		self.cal_vp.parameters.screen.clear()
		VisionEgg.Core.swap_buffers()
		
		
	def draw_cal_target(self, x, y): 
		for stimulus in self.cal_vp.parameters.stimuli: stimulus.parameters.position=(x,self.height-y)			
		self.cal_vp.parameters.screen.clear()
		self.cal_vp.draw()
		VisionEgg.Core.swap_buffers()
		
	def cal_target_beep(self) : 
		#self.__target_beep__.play()
		pass
		
	def cal_done_beep(self,error) : 
		#if(error !=0):
		#	self.__target_beep__error__.play()
		#else:
		#	self.__target_beep__done__.play()
		pass
		
	def dc_done_beep(self,error) : 
		#if(error !=0):
		#	self.__target_beep__error__.play()
		#else:
		#	self.__target_beep__done__.play()
		pass
			
	def dc_target_beep(self) : 
		#self.__target_beep__.play()
		pass

	def translate_key_message(self,event):
		if event.type == KEYDOWN:
			if event.key == K_F1:  
				key = pylink.F1_KEY;
			elif event.key == K_F2:  
				key = pylink.F2_KEY;
			elif event.key == K_F3:  
				key = pylink.F3_KEY;
			elif event.key == K_F4:  
				key = pylink.F4_KEY;
			elif event.key == K_F5:  
				key = pylink.F5_KEY;
			elif event.key == K_F6:  
				key = pylink.F6_KEY;
			elif event.key == K_F7:  
				key = pylink.F7_KEY;
			elif event.key == K_8:  
				key = pylink.F8_KEY;
			elif event.key == K_F9:  
				key = pylink.F9_KEY;
			elif event.key == K_F10:  
				key = pylink.F10_KEY;
			elif event.key == K_PAGEUP:  
				key = pylink.PAGE_UP;
			elif event.key == K_PAGEDOWN:  
				key = pylink.PAGE_DOWN;
			elif event.key == K_UP:  
				key = pylink.CURS_UP;
			elif event.key == K_DOWN:  
				key = pylink.CURS_DOWN;
			elif event.key == K_LEFT:  
				key = pylink.CURS_LEFT;
			elif event.key == K_RIGHT:  
				key = pylink.CURS_RIGHT;
			elif event.key == K_BACKSPACE:  
				key = '\b';
			elif event.key == K_RETURN:  
				key = pylink.ENTER_KEY;
			elif event.key == K_ESCAPE:  
				key = pylink.ESC_KEY;
			elif event.key == K_TAB:  
				key = '\t';			
			else:
 				key = event.key;

			if key == pylink.JUNK_KEY:
				return 0
			return key	

		return 0

	def get_input_key(self):
		ky=[]
		for key in pygame.event.get([KEYDOWN]):
			print key.key
			try:
				tkey = self.translate_key_message(key)
				ky.append(KeyInput(tkey))
			except Exception, err:
				print err
		return ky
		
	def exit_image_display(self):
		self.image_vp.parameters.screen.clear()
		VisionEgg.Core.swap_buffers()
		
	def alert_printf(self,msg): 
		print "alert_printf"		
	
	def setup_image_display(self, width, height):
		self.img_size = (width,height)
		self.image_vp.parameters.screen.clear()
		#VisionEgg.Core.swap_buffers()
		
	def image_title(self, threshold, text): 
		self.image_vp.parameters.stimuli[0].parameters.text=text			
		
	def draw_image_line(self, width, line, totlines,buff):		
		i =0
		while i <width:
			if buff[i]>=len(self.pal):
				buff[i]=len(self.pal)-1
			self.imagebuffer.append(self.pal[buff[i]&0x000000FF])
			i= i+1
		
		if line == totlines:	
			img =Image.new("RGBX",self.img_size)
			img.fromstring(self.imagebuffer.tostring())
			img = img.resize(self.image_vp.parameters.stimuli[1].parameters.size)
			
			self.draw_cross_hair(img)
			
			self.image_vp.parameters.stimuli[1].texture_object.put_sub_image(img)			

			self.image_vp.parameters.screen.clear()
			self.image_vp.draw()
			
			VisionEgg.Core.swap_buffers()

			self.imagebuffer = array.array('l')
					
	def draw_cross_hair(self, img):
		xdata = self.tracker.getImageCrossHairData()
		
		if xdata is None:
			return
		else:
			idraw = PIL.ImageDraw.Draw(img)

			l =0
			t =0
			w = img.size[0]
			h = img.size[1]
			wmax = w/6
			wmin = wmax/3
			thick = 1 + (w/300)

			white = (255,255,255)
			green = (0,255,0)
			blue = (0,0,255)
			
			channel = xdata[0]
			x = xdata[1]
			y = xdata[2]
			for i in range(4):#resize to rendered size
			    if(x[i] != 0x8000):
				x[i] = (w*x[i])/8192
				y[i] = (h*y[i])/8192
			
			if(channel == 2):                 # head camera channel: draw marker xhairs 
				for i in range(4):
					if(x[i] != 0x8000):
				    		hline(idraw, (x[i]-wmax), (x[i]+wmax), y[i],        white)
				    		vline(idraw, x[i],        (y[i]-wmax), (y[i]+wmax), white)
				    		
			else:
				if(x[0] != 0x8000):     # pupil (full-size) xhair
					hline(idraw, l,   (l+w), y[0],white)
					vline(idraw, x[0],t,    (t+h),white)
					
				if(x[1] != 0x8000):     # CR (open) xhair
					hline(idraw, (x[1]-wmax), (x[1]-wmin), y[1],blue);
					hline(idraw, (x[1]+wmin), (x[1]+wmax), y[1],blue);
					vline(idraw,  x[1],(y[1]-wmax), (y[1]-wmin),blue);
					vline(idraw,  x[1],(y[1]+wmin), (y[1]+wmax),blue);
				    	
				if(x[2] != 0x8000):     # pupil limits box
					hline(idraw, x[2], x[3], y[2],green);
					hline(idraw, x[2], x[3], y[3],green);
					vline(idraw, x[2], y[2], y[3],green);
					vline(idraw, x[3], y[2], y[3],green);

			del idraw 

	def set_image_palette(self, r,g,b): 
		self.imagebuffer = array.array('l')
		self.clear_cal_display()
		sz = len(r)
		i =0
		self.pal = []
		while i < sz:
			rf = int(b[i])
			gf = int(g[i])
			bf = int(r[i])
			self.pal.append((rf<<16) | (gf<<8) | (bf))
			i = i+1

