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
# $Date: 2005/11/01 13:16:09 $
# 
#



import pygame
import pygame.mixer
import pygame.event
import pygame.image
import pygame.draw
import array
import Image
import pylink
from pygame.constants import *





class KeyInput:
	def __init__(self,key,state=0):
		self.__key__ = key
		self.__state__ =state
		self.__type__= 0x1


def vline(surf,x,y0,y1,col):
	pygame.draw.line(surf,col,(x,y0),(x,y1))
	
def hline(surf,x0,x1,y,col):
	pygame.draw.line(surf,col,(x0,y),(x1,y))
	
	
class EyeLinkCoreGraphicsPyGame(pylink.EyeLinkCustomDisplay):
	def __init__(self,w,h, tracker):
		pylink.EyeLinkCustomDisplay.__init__(self)
		pygame.display.init()
		pygame.mixer.init()
		pygame.display.set_mode((w, h), FULLSCREEN |DOUBLEBUF |RLEACCEL |DOUBLEBUF ,16)
		self.__target_beep__ = pygame.mixer.Sound("caltargetbeep.wav")
		self.__target_beep__done__ = pygame.mixer.Sound("caltargetbeep.wav")
		self.__target_beep__error__ = pygame.mixer.Sound("caltargetbeep.wav")
		self.imagebuffer = array.array('l')
		self.pal = None	
		self.size = (0,0)
		if(not pygame.font.get_init()):
			pygame.font.init()
		self.fnt = pygame.font.Font("cour.ttf",25)
		self.fnt.set_bold(1)
		self.tracker = tracker
	


	def setup_cal_display (self):
		surf = pygame.display.get_surface()
		surf.fill((255,255,255,255))
		pygame.display.flip()
		
		
	def exit_cal_display(self): 
		self.clear_cal_display()
		
	def record_abort_hide(self):
		pass

	def clear_cal_display(self): 
		surf = pygame.display.get_surface()
		surf.fill((255,255,255,255))
		pygame.display.flip()	
		surf.fill((255,255,255,255))
		
	def erase_cal_target(self):
		surf = pygame.display.get_surface()
		surf.fill((255,255,255,255))
		
		
	def draw_cal_target(self, x, y): 
		outsz=10
		insz=4
		surf = pygame.display.get_surface()
		#surf.fill((0,0,0,255),(x,y,20,20))
		rect = pygame.Rect(x-outsz,y-outsz,outsz*2,outsz*2)
		pygame.draw.ellipse(surf,(0,0,0), rect)	
		rect = pygame.Rect(x-insz,y-insz,insz*2,insz*2)
		pygame.draw.ellipse(surf,(255,255,255), rect)	
		pygame.display.flip()
		
	def cal_target_beep(self) : 
		self.__target_beep__.play()
		
	def cal_done_beep(self,error) : 
		if(error !=0):
			self.__target_beep__error__.play()
		else:
			self.__target_beep__done__.play()
		
	def dc_done_beep(self,error) : 
		if(error !=0):
			self.__target_beep__error__.play()
		else:
			self.__target_beep__done__.play()
			
	def dc_target_beep(self) : 
		self.__target_beep__.play()
	
	
	
	
	def get_input_key(self):
		ky=[]
		for key in pygame.event.get([KEYDOWN]):
			keycode = key.key
			if keycode == K_F1:  keycode = pylink.F1_KEY
			elif keycode ==  K_F2:  keycode = pylink.F2_KEY
			elif keycode ==   K_F3:  keycode = pylink.F3_KEY
			elif keycode ==   K_F4:  keycode = pylink.F4_KEY
			elif keycode ==   K_F5:  keycode = pylink.F5_KEY
			elif keycode ==   K_F6:  keycode = pylink.F6_KEY
			elif keycode ==   K_F7:  keycode = pylink.F7_KEY
			elif keycode ==   K_F8:  keycode = pylink.F8_KEY
			elif keycode ==   K_F9:  keycode = pylink.F9_KEY
			elif keycode ==   K_F10: keycode = pylink.F10_KEY

			elif keycode ==   K_PAGEUP: keycode = pylink.PAGE_UP
			elif keycode ==   K_PAGEDOWN:  keycode = pylink.PAGE_DOWN
			elif keycode ==   K_UP:    keycode = pylink.CURS_UP
			elif keycode ==   K_DOWN:  keycode = pylink.CURS_DOWN
			elif keycode ==   K_LEFT:  keycode = pylink.CURS_LEFT
			elif keycode ==   K_RIGHT: keycode = pylink.CURS_RIGHT

			elif keycode ==   K_BACKSPACE:    keycode = ord('\b')
			elif keycode ==   K_RETURN:  keycode = pylink.ENTER_KEY
			elif keycode ==   K_ESCAPE:  keycode = pylink.ESC_KEY
			elif keycode ==   K_TAB:     keycode = ord('\t')
  			elif(keycode==pylink.JUNK_KEY): keycode= 0
			ky.append(KeyInput(keycode))
		return ky
		
	def exit_image_display(self):
		self.clear_cal_display()
		
	def alert_printf(self,msg): 
		print "alert_printf"
		
		
		
	
	def setup_image_display(self, width, height):
		self.size = (width,height)
		self.clear_cal_display()
		
	def image_title(self, threshold, text): 
		text = text + " " +str(threshold)

		sz = self.fnt.size(text[0])
		txt = self.fnt.render(text,len(text),(0,0,0,255), (255,255,255,255))
		surf = pygame.display.get_surface()
		imgsz=(self.size[0]*3,self.size[1]*3)
		topleft = ((surf.get_rect().w-imgsz[0])/2,(surf.get_rect().h-imgsz[1])/2)
		imsz=(topleft[0]+imgsz[0]/2,topleft[1]+imgsz[1]+10)
		surf.blit(txt, imsz)
		pygame.display.flip()
		surf.blit(txt, imsz)
		
	

	def draw_cross_hair(self, surf):
		xdata = self.tracker.getImageCrossHairData()
		if xdata is None:
			return
		else:
			l =0
			t =0
			w = surf.get_rect().w
			h = surf.get_rect().h
			wmax = w/6
			wmin = wmax/3
			thick = 1 + (w/300)

			col = (255,255,255,255)
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
				    		hline(surf, (x[i]-wmax), (x[i]+wmax), y[i],        col)
				    		vline(surf, x[i],        (y[i]-wmax), (y[i]+wmax), col)
				    		
			else:
				if(x[0] != 0x8000):     # pupil (full-size) xhair
					hline(surf, l,   (l+w), y[0],col)
					vline(surf, x[0],t,    (t+h),col)
					
				if(x[1] != 0x8000):     # CR (open) xhair
					hline(surf, (x[1]-wmax), (x[1]-wmin), y[1],col);
					hline(surf, (x[1]+wmin), (x[1]+wmax), y[1],col);
					vline(surf,  x[1],(y[1]-wmax), (y[1]-wmin), col);
					vline(surf,  x[1],(y[1]+wmin), (y[1]+wmax), col);
				    	
				if(x[2] != 0x8000):     # pupil limits box
					hline(surf, x[2], x[3], y[2],col);
					hline(surf, x[2], x[3], y[3],col);
					vline(surf, x[2], y[2], y[3],col);
					vline(surf, x[3], y[2], y[3],col);
					
			
			    	
		
	def draw_image_line(self, width, line, totlines,buff):		
		#print "draw_image_line", len(buff)
		i =0
		while i <width:
			self.imagebuffer.append(self.pal[buff[i]])
			i= i+1
				
		
		if line == totlines:
			imgsz = (self.size[0]*3,self.size[1]*3)
			bufferv = self.imagebuffer.tostring()
			img =Image.new("RGBX",self.size)
			img.fromstring(bufferv)
			img = img.resize(imgsz)
			
			img = pygame.image.fromstring(img.tostring(),imgsz,"RGBX");
			self.draw_cross_hair(img)
			surf = pygame.display.get_surface()
			surf.blit(img,((surf.get_rect().w-imgsz[0])/2,(surf.get_rect().h-imgsz[1])/2))
			pygame.display.flip()
			self.imagebuffer = array.array('l')
			
			
		
			
		
		
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