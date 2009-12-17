# -*- coding: utf-8 -*-
"""Contains classes for presenting stimuli and instructions on the screen

displays.py defines the top-level Display class, along with child classes for specific types of stimuli

The data for a Display object may be accessed through dictionary notation. For instance, if d is a type of Display object (e.g. a TextDisplay) then
d['onset_time'] is the timestamp of the instant the display was shown (corresponding to the timestamps in the EyeLink data file)
d['swap_time'] is the time, in milliseconds, it took to show the display and start the response collectors. swap_time represents the uncertainty in onset_time and
               in rt. The correct onset time may be between onset_time and onset_time+swap_time, and the correct rt may be between reported rt and reported rt - swap_time.
If the response_collectors parameter was not explictly set when the display was created, then a response collector object would automatically be created and the data from
that response collector could be accessed from the display (e.g. d['acc'], d['rt'], etc.).  For details see the response_collectors.py docs and the description of the
response_device keyword in the Display.__init__ docs, below.
"""
import pygame, VisionEgg.Core, os, pylink, pygame.surfarray, pygame.image
from VisionEgg.Textures import Texture,TextureStimulus,TextureTooLargeError
from VisionEgg.Text import Text
from experiment import getExperiment,getLog,checkForResponse,getTracker,Error
import VisionEgg.GL as gl
from UserDict import DictMixin
from interest_area import InterestArea
from shapes import Rectangle
import codecs
try:
    import winsound
except:
    winsound = None

class Display(DictMixin):
    """Class for displaying a stimulus on the screen, usually for instructions or feedback to the user.

    Usually one of the subclasses of Display is used.
    
    In general the only things the EyeScript scripter will do with Display objects are create them, call their run method,
    and read their parameter values (e.g. rt).  All the other methods defined below are internal helper methods.
    """
    
    bgNumber = 0
    """Default ID assigned to screenshot and interest area files, incremented for each trial"""
    
    def __init__(self,stimulus=[],logging = None,**params):
        """Set up the VisionEgg viewport for eventual display, and set this object's parameters.

        Arguments (all except 'stimulus' are optional keyword arguments):
        stimulus:  a list of VisionEgg stimuli to display. (stimulus may be a different type for subclasses)
        bgcolor:  background color, over which the stimuli will be drawn; an RGB 3-tuple
        cresp: the correct response.  Default is False (no correct response).
               cresp=None means the correct response is to not respond; any response will be considered incorrect
        possible_resp: List of responses which will be accepted by the ResponseCollector. Any responses not in possible_resp will be ignored.
                       Set possible_resp = ['any'] to accept any response from the ResponseCollector's device
        logging: list of strings representing parameters and variables to record in the log files
                 may include 'rt','acc','resp','cresp','onset_time','swap_time', or any parameters of the object.
                 For example, having the argument logging=['rt','resp'] would result in the RT and the response being logged for this display
                 Default:  [] if cresp == False (no correct response), or ['rt','acc','resp','cresp'] if there is a correct response.
        name: the name to identify the display in the log files.
              For example, having the arguments name="question" and logging=['rt','resp'] would result in
              RTs and responses for this display being logged as, respectively, question.rt and question.resp
        duration: maximum time to show the display (in ms), or 'infinite' for no limit.
                  The stimulus will remain on the screen after the display terminates, until the next display is run.
        min_rt: Time before a response will be accepted (e.g. to prevent accidental rapid key repeats being accepted) 
        interest_areas: list of IA objects, specifying interest areas for Data Viewer analysis and for gaze-contingent experiments
                        Set to 'True' to calculate interest areas automatically (usually for text displays)
        background_for: Trial object for which this display defines the background image and interest areas.
                        This display's image and interest areas will be loaded for that trial in the EyeLink Data Viewer
        interest_area_file: filename for saving the interest areas. The file will be in data_directory (experiment parameter).
                            Default: a unique ID number prefixed with 'image_' if background_for is set; otherwise no interest area file will be written
        screen_image_file: filename for saving the screenshot of the display. The file will be in data_directory (experiment parameter).
                           Default: a unique ID number prefixed with "image_' if background_for is set; otherwise no screen image file will be written
        response_collectors: List of ResponseCollector objects to handle subjects' responses to the stimulus.
                             These response collectors will be started at the instant this display is shown, and this display will stop running
                             when the first response collector (if any) returns a response.
                             The stimulus will remain on the screen after the display terminates, until the next display is run.
                             Most often, response_device, below, will be used instead of response_collectors.
        response_device: The name of a class in response_collectors.py that will handle the subject's responses (e.g. Keyboard, ButtonBox, etc.).
                         If the response_collectors parameter is set, then response_device will have no effect.  Otherwise, response_collectors will be set
                         to a list containing (only) an object of the class specified by response_device. The parameters of that response collector object 
                         (e.g. cresp, possible_resp, duration, name, min_rt) are set by setting those keywords when the Display is created. The response collector object
                         will not log its own parameters (i.e. its logging parameter will be set to []) but the display object will inherit its parameters
                         (like rt, resp, acc, etc.) (except when the display object has a parameter of the same name, e.g. onset_time).
                         
                         Example:
                         
                         stim = TextDisplay(probe,response_device=ButtonBox,possible_resp=[1,2],cresp=1,duration=2000,name="probe",logging=['rt','resp','acc'])
                         stim.run()
                         if stim['acc']: TextDisplay("Correct! Response time: %s"%stim['rt']).run()
                         else: TextDisplay("Incorrect.").run()
                         
                         does the same thing as
                         
                         rc = ButtonBox(possible_resp=[1,2],cresp=1,duration=2000,name="probe",logging=['rt','resp','acc'])
                         TextDisplay(probe,response_collectors=[rc],duration=2000).run()
                         if rc['acc']: TextDisplay("Correct! Response time: %s"%rc['rt']).run()
                         else: TextDisplay("Incorrect.").run()
        """
        # Parameters not set with keywords to __init__ will default to the experiment object's parameters (which default to the values in defaults.py)
        self.params = getExperiment().params.copy()
        self.update(params)
        
        self.setdefault('name',self.__class__.__name__)
        
        # If the response_collectors keyword wasn't set, then create a response collector of the class specified by response_device, with the keywords passed to __init__
        if self.get('response_collectors',None) == None:
            self['response_collectors'] = [self['response_device'](**params.copy())]
            
            self.auto_response_collector = True # Remember that we automatically created the response collector
            # If auto_response_collector == True then the display will inherit the response collector's data (see the __getitem__ method below)
            
            self['response_collectors'][0].logging = [] # The display can log the data it inherits from the response collector
            # so having the response collector do logging would be redundant
            
        else:
            self.auto_response_collector = False
        
        self.params.setdefault('duration',"infinite")
            
        if logging == None:
            # Defaults for logging
            # If cresp was set and if we can log data inherited from an automatically created response collector, then log rt, acc, resp, and cresp; otherwise no logging.
            self.logging = (self.get('cresp',False) != False and self.auto_response_collector) and ['rt','acc','resp','cresp'] or []
        else:
            self.logging = logging
        

        self.prepareStimulus(stimulus) # prepareStimulus is defined differently for each child class

        if self.get('background_for',None):
            # If this display is going to be the background image for a trial in the Data Viewer, then create unique names for the screenshot and interest area files
            # if the names were not already set through keywords
            Display.bgNumber += 1
            self.setdefault('screen_image_file',
                            os.path.join(getExperiment()['data_file_root_name']+"_screenimages","image_%s%sjpg"%(Display.bgNumber,os.extsep)))
            if self.get('interest_areas',None):
                self.setdefault('interest_area_file',
                                os.path.join(getExperiment()['data_file_root_name']+"_interest_areas","image_%s%sias"%(Display.bgNumber,os.extsep)))
            self['background_for'].dataViewerBG = self # Let the trial know that this display will be its background image
            
        if self.get('screen_image_file',None):
            self.write_screen_image_file(os.path.join(getExperiment()['data_directory'],self['screen_image_file']))
        if self.get('interest_area_file',None):
            self.write_interest_area_file(os.path.join(getExperiment()['data_directory'],self['interest_area_file']))
                
    def prepareStimulus(self,stimulus):
        """helper method, not directly called in EyeScript scripts in general.
        
        Takes a 'stimulus' argument passed from init and returns a list of VisionEgg stimuli for display.

        For a Display object, you would create the VisionEgg stimulus list beforehand and pass it to Display's init method.
        For child classes, 'stimulus' is generally a file or string used to generate the VisionEgg stimuli.
        """
        return stimulus

    def draw(self,onset=None):
        """helper method, not directly called in EyeScript scripts in general.
        
        Actually draw the display to the screen.
        
        As the display is drawn, record onset_time and swap_time, start the response collectors, and inform the eyetracker
        
        Optional argument: onset, time in milliseconds when the screen is to be displayed (from the same baseline as for the times 
        returned by pylink.currentTime() and recorded in the eyetracker data file)
        """
        self.drawToBuffer()
        while pylink.currentTime() < onset: checkForResponse()
        self['onset_time']=pylink.currentTime()
        VisionEgg.Core.swap_buffers()
        for rc in self['response_collectors']: rc.start()
        self['swap_time']=pylink.currentTime()-self['onset_time']
        getTracker().sendMessage("%s.SYNCTIME %d"%(self['name'],pylink.currentTime()-self['onset_time']))

    def run(self,onset=None):
        """Draws the screen and collects the response.
        
        Optional argument: onset, time in milliseconds when the stimulus is to be displayed (from the same baseline as for the times
        returned by pylink.currentTime() and recorded in the eyetracker data file).
        
        The onset argument will typically be used to precisely space out displays.  For example, the following code will cause a second display to be shown
        precisely 500 milliseconds after a first display is shown.
        
        d1 = TextDisplay(stim1,duration = 0,response_collector = [rc])
        d2 = TextDisplay(stim2)
        d1.run()
        d2.run(onset = d1['onset_time']+500)
        """
        checkForResponse() # Clears the pygame event buffer
        self.draw(onset=onset)
        while self['duration'] == 'infinite' or pylink.currentTime() < self['onset_time'] + self['duration']:
            responses = checkForResponse()
            if [rc for rc in self['response_collectors'] if rc in responses]: break
        for rc in self['response_collectors']:
            if rc['duration'] == 'stimulus': rc.stop()
        checkForResponse() # This will stop any response collectors whose duration equals this display's duration
        self.log()
    def log(self):
        """helper method, not directly called in EyeScript scripts in general.
        
        Record the parameters specified in the 'logging' attribute in the txt behavioral data and edf eyetracker data files
        """
        getLog().logAttributes(**dict([("%s.%s"%(self['name'],param),self[param]) for param in self.logging]))

    def drawToBuffer(self):
        """helper method, not directly called in EyeScript scripts in general.
        
        Helper method that draws the display to a buffer.
        
        The buffer may be swapped to the screen to show the display, or saved as a screenshot.
        """
        # set the background color
        t1 = pygame.time.get_ticks()
        getExperiment().screen.parameters.bgcolor = self['bgcolor']
        # clear the screen (with the background color)
        getExperiment().screen.clear()
        t2 = pygame.time.get_ticks()
        # draw the viewport
        self.viewport.draw()
##        t3 = pygame.time.get_ticks()
##        # Workaround for VisionEgg bug where text stimuli sometimes don't get displayed.
##        # I have no idea why this works, but it disappears the bug.
##        gl.glReadPixels(0,0,getExperiment()['screen_size'][0],getExperiment()['screen_size'][1]
##                        ,gl.GL_RGBA,gl.GL_UNSIGNED_BYTE
##                        )
##        t4 = pygame.time.get_ticks()
##        getExperiment().screen.clear()
##        t5 = pygame.time.get_ticks()
##        self.viewport.draw()
##        t6 = pygame.time.get_ticks()
##        print ("%s %s %s %s %s"%(t2-t1,t3-t2,t4-t3,t5-t4,t6-t5))

    def write_screen_image_file(self,filename):
        """helper method, not directly called in EyeScript scripts in general.
        
        Save a screenshot of the display
        
        Argument: the filename for the screenshot
        """
        self.drawToBuffer()
        image = getExperiment().screen.get_framebuffer_as_image()
        screensDirectory = os.path.dirname(filename)
        if screensDirectory and not os.path.isdir(screensDirectory): os.makedirs(screensDirectory)
        image.save(filename)

    def write_interest_area_file(self,filename):
        """helper method, not directly called in EyeScript scripts in general.
        
        Write the coordinates of the display's interest areas to a file readable by the Data Viewer
        
        Argument: the filename for the interest area file
        """
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory): os.makedirs(directory)
        iaFile = codecs.open(filename,'w','utf8')
        for i,ia in enumerate(self['interest_areas']):
            iaFile.write("%s\t%s\t%s\t%s\n"%(ia.shapeName(),i+1,ia.coordinateString(),ia.label))
        iaFile.close()

    
    def __getitem__(self,name):
        """helper method, not directly called in EyeScript scripts
        
        Allows the display's parameters to be accessed using dictionary notation.
        
        If the display does not have the parameter and if a response collector object was automatically created with the response_device keyword, then
        the value of the response collector's parameter will be returned (e.g. rt, acc, etc.)
        """
        if self.params.has_key(name) or not getattr(self,'auto_response_collector',False):
            return self.params[name]
        else:
            return self.params['response_collectors'][0][name]

    def __setitem__(self,name,value):
        """helper method, not directly called in EyeScript scripts
        
        Allows the display's parameters to be set using dictionary notation
        """
        self.params[name]=value

    def keys(self):
        """helper method, not directly called in EyeScript scripts
        
        Returns a list of the parameter names of the display
        """
        if getattr(self,'auto_response_collector',False):
            combinedDict = self.params.copy()
            combinedDict.update(self.params['response_collectors'][0].params)
            return combinedDict.keys()
        else:
            return self.params.keys()
            

class TextDisplay(Display):
    """Shows text on the screen, and collects a response.

    When creating a TextDisplay object, the 'stimulus' argument should be a string containing the text to display.

    Attributes: viewport, bgcolor, params inherited from Display

    Parameters in 'params' (keywords optionally specified when creating the object):
    margins:  a 4-tuple specifying width of the margins in pixels, of the form (left, top, right, bottom)
    align:  a 2-tuple specifying the horizontal and vertical alignment of the text.
            align[0] = 'left', 'center', or 'right' and align[1] = 'top', 'center', or 'bottom'
    wrap:  a boolean specifying whether or not to wrap the text
    font_name:  the name of a font file
    font_size:  point size of the font
    color:  the color of the font as an RGB 3-tuple
    vertical_spacing:  the distance in pixels between successive lines of text
    bgcolor, duration:  same as in Display
    """

    def prepareStimulus(self, text):
        """helper method, not directly called in EyeScript scripts in general.
        
        Takes a string and returns a list of VisionEgg Text objects, wrapped as necessary
        
        prepareStimulus also calculates interest areas if the interest_area_file parameter has been set (and if interest areas have not already been set)
        """
        
        margins = self['margins']
        align = self['align']
        textparams = {'font_size':self['font_size'],
                      'font_name':(pygame.font.match_font(self['font_name'],self['bold'],self['italic']) or self['font_name']),
                      'color':self['color']
                      }
      
        # height will be the total height of all the lines of text
        height = 0
        stimulus = []
        
        lines = [line.rstrip('\n') or " " for line in text.split('\n')]
        lines.reverse()
        self.wrap = False
        screenwidth = getExperiment()['screen_size'][0]-margins[0]-margins[2]
        wordwidths = []
        rightedges = []
        calculateIAs = self.get('interest_areas',False) == True or (self.get('interest_area_file',False) and
                                                                    self.get('interest_areas',True) == True
                                                                    )
        while lines:
            line = lines.pop()
            linelen = len(line.split())
            wordwidths.append([])
            rightedges.append([])
            lineText = None
            if calculateIAs:
                for i in range(linelen):
                    # Find the width of the first i+1 words
                    try:
                        firstwords = Text(text=line.rsplit(None,linelen-i-1)[0],**textparams)
                    except TextureTooLargeError:
                        if i==0: raise WordTooLargeError(line.split()[0])
                        break
                    rightedge = firstwords.parameters.size[0]
                    if rightedge > screenwidth:
                        if i==0: raise WordTooLargeError(line.split()[0])
                        lines.append(line.split(None,i)[-1])
                        break
                    wordwidths[-1].append(Text(text=line.split()[i],**textparams).parameters.size[0])
                    rightedges[-1].append(rightedge)
                    lineText = firstwords
                    
            else: # If we're not calculating interest areas
                # then try to estimate where the line breaks should be from the width of the text
                # This is generally much faster than the method above.
                testString = line
                wordsFitting = ""
                wordsFittingWidth = 0
                wordsFittingCount = 0
                wordsNotFittingCount = 1 + len(testString.split())
                while True:
                    try:
                        testText = Text(text=testString,**textparams)
                    except TextureTooLargeError:
                        wordsNotFitting = testString
                        wordsNotFittingWidth = None
                        wordsNotFittingCount = len(testString.split())
                        if wordsNotFittingCount == 1 + wordsFittingCount: break
                        runOffPoint = (len(wordsNotFitting) + len(wordsFitting)) / 2
                    else:
                        testSize = testText.parameters.size[0]
                        if testSize > screenwidth:
                            wordsNotFitting = testString # wordsNotFitting holds the smallest part of the line so far that we've found doesn't fit.
                            wordsNotFittingWidth = testSize
                            wordsNotFittingCount = len(testString.split())
                        else:
                            wordsFitting = testString # wordsFitting holds the largest part of the line so far that we've found fits on the screen.
                            wordsFittingWidth = testSize
                            wordsFittingCount = len(testString.split())
                            lineText = testText
                        
                        if wordsNotFittingCount <= 1 + wordsFittingCount:
                            # We've found the largest part of the line that will fit on the screen -- if we add one more word it won't fit.
                            # wordsNotFittingCount could be equal to wordsFittingCount if we stripped whitespace off the end of a line to make it fit.
                            break
                        
                        #Interpolate between wordsNotFitting and wordsFitting to estimate the index of the first character that runs off the screen
                        if wordsNotFittingWidth: # If we know the width of wordsNotFitting
                            # then interpolate based on the widths of wordsFitting and wordsNotFitting
                            runOffPoint = int((len(wordsNotFitting) - len(wordsFitting)) *
                                              (screenwidth - wordsFittingWidth) / (wordsNotFittingWidth - wordsFittingWidth)
                                              ) + len(wordsFitting)
                        else:
                            # If we don't know the width of wordsNotFitting (because of a TextureTooLargeError)
                            # then extrapolate based on the width of wordsFitting
                            runOffPoint = min(int(len(wordsFitting) * screenwidth / wordsFittingWidth),len(wordsNotFitting))
                    # Find the word containing our estimate of the first character running off the screen
                    try:
                        runOffWord = line[runOffPoint:].split()[0]
                    except IndexError: # The line ends in whitespace so the split yields the empty string
                        runOffWord = ""
                    testString = line[:runOffPoint] + runOffWord
                    # Have we already tested a string of this length?
                    if len(testString) >= len(wordsNotFitting):
                        # Then test the words up to the first word known not to fit.
                        testString = line.rsplit(None,linelen-(wordsNotFittingCount-1))[0]
                if wordsFitting == "" and line: raise WordTooLargeError(line.split()[0])
                if wordsFitting != line: lines.append(line.split(None,wordsFittingCount)[-1]) # Add the part that didn't fit as a new line

            stimulus.append(lineText or Text(text=" ",**textparams))
        height = sum([lineText.parameters.size[1] for lineText in stimulus])+self['vertical_spacing']*(len(stimulus) - 1)
            
        
        if align[1]=='top':
            ypos = getExperiment()['screen_size'][1]-margins[1]
        elif align[1] == 'bottom':
            ypos = margins[3] + height
        elif align[1] == 'center':
            ypos = (getExperiment()['screen_size'][1] + margins[3] - margins[1] + height) / 2
        else:
            raise "TextDisplay %s: invalid argument for align: %s"%(self['name'],align[1])

        self.setdefault('interest_area_labels',text.split())
        self['interest_areas'] = []
        for linenum,textline in enumerate(stimulus):
            ypos -= textline.parameters.size[1]
            linewidth = textline.parameters.size[0]
            #Calculate the position of the line on the screen
            # xpos is the x coordinate of the left edge of the line
            if align[0]=='left':
                xpos = margins[0]
            elif align[0]=='right':
                xpos = getExperiment()['screen_size'][0]-margins[2]-linewidth
            elif align[0]=='center':
                xpos = (getExperiment()['screen_size'][0] - margins[2] + margins[0] - linewidth)/2
            textline.set(position=(xpos,ypos))
            
            # Calculate the coordinates of the interest areas
            if calculateIAs:
                for wordnum,rightedge in enumerate(rightedges[linenum]):
                    rightGazeError = xpos + rightedge + self['buffer_size']
                    if wordnum == len(rightedges[linenum]) - 1:
                        iaRight = rightGazeError
                    else:
                        rightMidspace = xpos + (rightedges[linenum][wordnum+1]-wordwidths[linenum][wordnum+1] + rightedge) / 2
                        iaRight = (self['ia_fill'] and [rightMidspace] or [min(rightMidspace,rightGazeError)])[0]
                    leftGazeError = xpos + rightedge - wordwidths[linenum][wordnum] - self['buffer_size']
                    if wordnum == 0:
                        iaLeft = leftGazeError
                    else:
                        leftMidspace = xpos + (rightedge - wordwidths[linenum][wordnum] + rightedges[linenum][wordnum-1])/2
                        iaLeft = (self['ia_fill'] and [leftMidspace] or [max(leftMidspace,leftGazeError)])[0]
                    topGazeError = getExperiment()['screen_size'][1]-ypos-textline.parameters.size[1]-self['buffer_size']
                    if linenum == 0:
                        iaTop = topGazeError
                    else:
                        topMidspace = getExperiment()['screen_size'][1]-ypos-textline.parameters.size[1]-self['vertical_spacing']/2
                        iaTop = (self['ia_fill'] and [topMidspace] or [max(topMidspace,topGazeError)])[0]
                    bottomGazeError = getExperiment()['screen_size'][1]-ypos+self['buffer_size']
                    if linenum == len(stimulus)-1:
                        iaBottom = bottomGazeError
                    else:
                        bottomMidspace = getExperiment()['screen_size'][1]-ypos+self['vertical_spacing']/2
                        iaBottom = (self['ia_fill'] and [bottomMidspace] or [min(bottomMidspace,bottomGazeError)])[0]
                    if self.get('interest_area_labels',None):
                        try:
                            iaLabel = self['interest_area_labels'][len(self['interest_areas'])]
                        except IndexError:
                            raise InterestAreaLabelError("Not enough interest area labels provided for text: %s"%text)
                    else:
                        iaLabel = text.split()[len(self['interest_areas'])]
                    self['interest_areas'].append(InterestArea(Rectangle((iaLeft,iaTop,iaRight-iaLeft,iaBottom-iaTop)),label=iaLabel))

                    
            ypos-=self['vertical_spacing']

        self.viewport = fullViewport(stimulus)


class AudioPresentation(Display):
    """
    Class for presenting audio stimuli.

    When creating the AudioPresentation, you can set the keyword audio_package to either 'winsound' or 'pygame'
    to specify the Python package to use for sound playback. (If you omit the audio_package keyword, the experiment default will be used).
    winsound has low latency with low variance (consistently 14-15 ms on psyc-rickl04
    However winsound only works on Windows, and will cut off any files that are longer than one minute.
    pygame doesn't have those drawbacks, but it has really bad latency (mean 89 ms, SD 29 ms).

    See http://www.freelists.org/archives/visionegg/02-2008/msg00000.html for a discussion of other audio playback options (all problematic).

    If the duration keyword is set to "stimulus" then the sound will stop running when the AudioPresentation stops running (e.g. from a response),
    and vice versa.  Otherwise, the sound will keep playing after the AudioPresentation stops running.
    (This seems clumsy; may want a more elegant solution in the future which generalizes to video.)

    Setting duration to "stimulus" DOES NOT WORK if audio_package is 'winsound'; it acts the same as duration = 0.
    

    """
     
    def prepareStimulus(self,audiofile):
        """helper method, not directly called in EyeScript scripts in general.
        """
        if self['audio_package'] == 'winsound':
            self.audiofile = audiofile
            self.channel = None
        elif self['audio_package'] == 'pygame':
            try:
                self.sound = pygame.mixer.Sound(audiofile)
            except pygame.error, e:
                raise IOError("Pygame error '%s' trying to read audio file '%s'"%(e,audiofile))        
            self.channel = None
        else:
            raise "audio_package should be set to either 'winsound' or 'pygame'"
            
    def draw(self,onset=None):
        """helper method, not directly called in EyeScript scripts in general.
        
        Actually present the audio stimulus
        
        As it's presented, record onset_time and swap_time, start the response collectors, and inform the eyetracker
        
        Optional argument: onset, time in milliseconds when the stimulus is to be displayed (from the same baseline as for the times 
        returned by pylink.currentTime() and recorded in the eyetracker data file)
        """
        while onset and pylink.currentTime() < onset - self['audio_latency']: checkForResponse()
        self['onset_time']=pylink.currentTime() + self['audio_latency']
        for rc in self['response_collectors']: rc.start()
        if self['audio_package'] == 'winsound' and winsound:
            winsound.PlaySound(self.audiofile,winsound.SND_ASYNC | winsound.SND_FILENAME)
        elif self['audio_package'] == 'pygame':
            self.channel = self.sound.play()
        self['swap_time']=pylink.currentTime()-self['onset_time']
        getTracker().sendMessage("%s.SYNCTIME %d"%(self['name'],pylink.currentTime()-self['onset_time']))
    
    def run(self,onset=None):
        checkForResponse() # Clears the pygame event buffer
        self.draw(onset=onset)
        while ((self['duration'] in ['infinite','stimulus'] or pylink.currentTime() < self['onset_time'] + self['duration'])
               and not (self['duration'] == 'stimulus' and (not self.channel or not self.channel.get_busy()))
               ):
            responses = checkForResponse()
            if [rc for rc in self['response_collectors'] if rc in responses]: break

        if self['duration'] == 'stimulus': self.stop()
        
        for rc in self['response_collectors']:
            if rc['duration'] == 'stimulus': rc.stop()
        
        checkForResponse() # This will stop any response collectors whose duration equals this display's duration
        
        self.log()

    def stop(self):
        """
        Stop playback of the audio clip
        """
        if self.channel: self.channel.stop()

class ImageDisplay(Display):
    """Displays an image and collects a response.

    When creating an ImageDisplay object, the 'stimulus' argument should be a filename or a file-like object specifying
    the image to display.

    Parameters:  align, margins, bgcolor (same as in TextDisplay)
    """
    def prepareStimulus(self,imagefile):
        """helper method, not directly called in EyeScript scripts in general.
        
        Private helper method which takes a filename or file-like object and returns a TextureStimulus"""
        tex=Texture(pygame.image.load(imagefile))
        aligndictx = {'left':0,'center':.5,'right':1}
        aligndicty = {'top':0,'center':.5,'bottom':1}
        align=self['align']
        margins=self['margins']
        self.viewport = fullViewport([TextureStimulus(texture=tex,mipmaps_enabled = False,position=(
                    aligndictx[align[0]]*(getExperiment()['screen_size'][0]-tex.size[0]-margins[0]-margins[2])+margins[0],
                    aligndicty[align[1]]*(getExperiment()['screen_size'][1]-tex.size[1]-margins[1]-margins[3])+margins[1]
                    )
                                                      )
                                     ])

class SlideDisplay(Display):
    """
    Display a set of images and / or text stimuli at once.
    
    The __init__ method of SlideDisplay takes a list of other Display objects as arguments.
    The stimuli in those Display objects are combined and displayed together at runtime.
    The parameters of the component Display objects (e.g. duration, response_collectors) are ignored except for those parameters
    that affect the appearance of the stimulus (e.g. align, margins, etc.)
    
    Currently only TextDisplay and ImageDisplay objects may be incorporated in a SlideDisplay.  TO-DO:  add audio.
    """
    def prepareStimulus(self,components):
        """helper method, not directly called in EyeScript scripts in general."""
        stimulus = []
        self['interest_areas'] = []
        iaLabels = []
        for component in components:
            stimulus.extend(component.viewport.parameters.stimuli)
            if component.has_key('interest_areas'):
                self['interest_areas'].extend(component['interest_areas'])
                iaLabels.extend(component['interest_area_labels'])
        self.setdefault('interest_area_labels',iaLabels)
        self.viewport = fullViewport(stimulus)

class ContinueDisplay(SlideDisplay):
    """Shows text and diplays a continue message after a short delay.

    Responses are accepted and recorded after the continue message appears.

    Same attributes and parameters as TextDisplay, with two additional parameters:
    continue_text:  the text to display at the bottom of the screen after a delay (e.g. "Press any key to continue.")
    continue_delay:  the delay, in ms, before the continue text is displayed and responses are accepted.
    """
    def prepareStimulus(self,text):
        """helper method, not directly used in EyeScript scripts in general.
        """
        continueParams = self.params.copy()
        continueParams['align']=('center','bottom')
        firstParams = self.params.copy()
        firstParams['response_collectors'] = []
        firstParams['duration'] = self['continue_delay']
        self.display1 = TextDisplay(text,logging = [],**firstParams)
        SlideDisplay.prepareStimulus(self,[self.display1,TextDisplay(self['continue_text'],**continueParams)])

    def draw(self,onset=None):
        """helper method, not directly used in EyeScript scripts in general.
        
        Draws the text, and then after a delay, redraws the text with a continue message.
        """
        self.display1.draw(onset=onset)
        SlideDisplay.draw(self,onset=self.display1['onset_time']+self['continue_delay'])
        self['onset_time'] = self.display1['onset_time']
        self['swap_time'] = self.display1['swap_time']

class InterestAreaLabelError(Error):
    """Utility class not directly used in EyeScript scripts
    
    Error class to signal not enough interest area labels provided to label interest areas in a display.
    """
    pass
class WordTooLargeError(Error):
    """Utility class not directly used in EyeScript scripts
    
    Error class to signal that a word in a TextDisplay was too large to fit on the screen.
    """
    pass

def fullViewport(stimuli):
    """Helper function, not directly used in EyeScript scripts in general.
    
    Make a VisionEgg Viewport covering the whole screen.
    """
    return VisionEgg.Core.Viewport(screen=getExperiment().screen,size=getExperiment().screen.size,stimuli=stimuli)
