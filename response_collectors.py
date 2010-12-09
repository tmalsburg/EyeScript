# -*- coding: utf-8 -*-
"""Contains classes for accepting and logging input via various modalities.
    
    response_collectors.py defines the abstract ResponseCollector class and modality-specific response collector classes inheriting from ResponseCollector.

    For scripts in which response collection always coincides with the display of a stimulus (the usual case),
    the script would generally not need to directly create or interact with response collectors.
    Display objects automatically create response collector objects to collect responses to the stimulus displayed,
    unless the response_collectors parameter of the Display object is explicitly set.
    The type of ResponseCollector object automatically created is set by the response_device parameter.
    For instance, TextDisplay("Button 1 or 2?", response_device = ButtonBox, possible_resp = [1,2], cresp = 1)
    would result in a ButtonBox object (inheriting from ResponseCollector) being created,
    whose possible_resp and cresp parameters would be set to [1,2] and 1 respectively.
    This ButtonBox object would start collecting responses at the onset of the TextDisplay,
    and the TextDisplay's run method would return when the ButtonBox object returned a response.
    
    Response collector objects would need to be created directly in the script if, for instance:
       More than one response needs to be collected after a stimulus display (e.g. in a dual-task experiment)
       Response collection needs to continue after the stimulus is done displaying
       Some parameters of the ResponseCollector can only be set after the associated Display object is created
          (in particular, if the possible_resp and/or cresp parameters of a ContinuousGaze response collector object are interest areas
           calculated when the associated Display object is created)
    
    You can access the data of a response collector object using the notation of Python dictionaries.
    For instance, if rc is a type of ResponseCollector, say a Keyboard object, then
    rc['rt'] is the response time (in milliseconds) for the keyboard response
    rc['resp'] is the subject's response (the key pressed)
    rc['cresp'] is the correct response if this was specified
    rc['acc'] is the accuracy (0 or 1) of the subject's keyboard response (if cresp was specified)
    rc['onset_time'] is the timestamp of the instant the response collector started accepting responses (corresponding to the timestamps in the EyeLink edf data files)
    rc['rt_time'] is the timestamp of the instant the response was made (corresponding to the timestamps in the Eyelink edf data files)
    
    You can also access any of the response collector's parameters through dictionary notation (e.g. rc['possible_resp'])
    though in most cases there would be no need to do this in an EyeScript script.
"""
import pygame
import pylink
from experiment import getExperiment,getTracker,getLog,setUpDevice,getDevice
from trials import TrialAbort
from UserDict import DictMixin
import devices
from constants import *
try:
    import pythoncom
    import speechRecognition
except ImportError:
    pythoncom = None
    speechRecognition = None

class ResponseCollector(DictMixin):
    """Abstract class for collecting responses from the subject, from which modality-specific response collector classes will inherit
    """

    def __init__(self,logging = None,**params):
        """Set parameters for the ResponseCollector, and initialize the input device if it hasn't already been initialized.
        
        Possible parameters:
        cresp: the correct response.  Default is False (no correct response).
               cresp=None means the correct response is to not respond; any response will be considered incorrect
        possible_resp: List of responses which will be accepted by the ResponseCollector. Any responses not in possible_resp will be ignored.
                       Set possible_resp = ['any'] to accept any response from the ResponseCollector's device
        logging: list of strings representing parameters and variables to record in the log files
                 may include 'rt','acc','resp','cresp','onset_time', or any parameters of the object.
                 For example, having the argument logging=['rt','resp'] would result in the RT and the response being logged for this ResponseCollector
                 Default:  [] if cresp == False (no correct response), or ['rt','acc','resp','cresp'] if there is a correct response.
        name: the name to identify the ResponseCollector in the log files.
              For example, having the arguments name="tone_response" and logging=['rt','resp','acc'] would result in
              RTs, responses, and accuracies for this ResponseCollector being logged as, respectively, tone_response.rt, tone_response.resp, and tone_response.acc
        duration: time limit in milliseconds for the subject to respond, or 'infinite' for no limit, or 'stimulus' to accept
                  responses only as long as the associated Display object is running. ('stimulus' is equivalent to
                  'infinite' if the response collector does not belong to any display.)
        min_rt: Time before a response will be accepted (e.g. to prevent accidental rapid key repeats being accepted) 
        """
        self.params = getExperiment().params.copy()
        self.update(params)
        self.setdefault('name',self.__class__.__name__)
        self.setdefault('cresp',False)
        self.setdefault('duration','stimulus')
        if logging == None:
            self.logging = self['cresp'] != False and ['rt','acc','resp','cresp'] or []
        else:
            self.logging = logging
        self['rt'] = self['resp'] = self['acc'] = None
        defaultDeviceName = self.__class__.__name__+"Device"
        if hasattr(devices,defaultDeviceName): setUpDevice(getattr(devices,defaultDeviceName))        
        
    def start(self):
        """Start accepting responses, and record the onset time of this ResponseCollector
        """
        self['onset_time'] = pylink.currentTime()
        self['resp'] = None
        getExperiment().response_collectors.append(self)
        self.running = True

    def respond(self,events):
        """Update status, given the latest events in the queue.
        
        The scripter will normally not need to directly call respond.
        Instead, call EyeScript's checkForResponse function (from the experiment module)
        which will ask each active input device to checkForResponse, which in turn will ask all ResponseCollectors for that device to checkForResponse.
        
        Returns: True if there is a response or if this ResponseCollector timed out, False otherwise
        """
        if self['duration'] not in ['infinite','stimulus'] and pylink.currentTime() >= self['onset_time'] + self['duration']: # timed out
            self.stop()
            return True
        if pylink.currentTime() >= self['min_rt'] + self['onset_time'] and True in [self.handleEvent(event) for event in events]:
            if self.params.get('cresp',False) != False: #There is a correct response, so log accuracy
                self.params['acc'] = int(self.params['resp']==self.params['cresp'])
            else: self.params['acc'] = None
            return True
        else: return False
    
    def handleEvent(self,event):
        """Defined by child classes to specify how to read input from the device and how to record the data from a response.
        
        handleEvent is responsible for recording the rt, rt_time, and resp attributes when a response is detected.
        
        Normally, response collection is stopped as soon as a response is detected, but sometimes response collection continues after that,
        e.g. until response offset is recorded.
        """
        pass
    
    def stop(self):
        """Log the subject's response, and stop monitoring for responses
        """
        if self.running:
            getExperiment().response_collectors.remove(self)
            if self.params.get('cresp',False) != False: #There is a correct response, so log accuracy
                self.params['acc'] = int(self.params['resp']==self.params['cresp'])
                print "  Response: %(resp)s (%(cresp)s)" % self.params
            self.log()
            self.running = False
        
    def log(self):
        """Record the subject's response in the log files
        
        Normally the scripter would not call log directly but would call stop instead which calls log
        """
        getLog().logAttributes(**dict([("%s.%s"%(self['name'],param),self[param]) for param in self.logging]))

    def __getitem__(self,name):
        """Allows retrieval of the object's parameters through dictionary notation
        """
        return self.params[name]

    def __setitem__(self,name,value):
        """Allows setting the object's parameters using dictionary notation
        """
        self.params[name]=value

    def keys(self):
        """Returns a list of the names of all the object's parameters
        """
        return self.params.keys()




class EyeLinkButtons(ResponseCollector):
    """Collect responses from the EyeLink buttons (currently [May 2007] connected to the EyeLink II)
    
    possible_resp may include 'X', 'Y', 'B', 'A', 'left thumb', 'left trigger', 'right trigger', and 'any'.
    """

            
    def handleEvent(self,event):
        if event.type == EYELINK_BUTTON_DOWN and (event.key in self['possible_resp'] or "any" in self['possible_resp']):
            self['rt'] = event.time-self['onset_time']
            self['rt_time'] = event.time
            self['resp'] = event.key         
            getTracker().sendMessage("%d %s.END_RT"%(self['rt_time']-pylink.currentTime(),self['name']))
            return True
        elif event.type == EYELINK_BUTTON_UP and event.key == self['resp']:
            self['rt_offset'] = event.time - self['onset_time']
            self['rt_offset_time'] = event.time
            getTracker().sendMessage("%d %s.offset"%(self['rt_offset_time']-pylink.currentTime(),self['name']))
            self.stop()
            return False
            
class Keyboard(ResponseCollector):
    """Collect a response from the keyboard and record the results
    """
    
    def handleEvent(self,event):
        """Check the buffer of keyboard input to see if an acceptable response was entered.
        
        If an acceptable response (i.e. listed in possible_resp) was detected, set the 'acc', 'resp', 'rt', and 'rt_time' parameters accordingly, and return True.
        Otherwise return False.
        """
        if event.type == KEYDOWN and ("any" in self['possible_resp'] or (pygame.key.name(event.key) in self['possible_resp'])):
            #We got a legal response; handle it appropriately
            self['rt_time'] = event.time
            getTracker().sendMessage("%s.END_RT"%(self['name']))
            self['rt'] = self['rt_time']-self['onset_time']
            self['resp'] = pygame.key.name(event.key)
            self.stop()
            return True
        return False

MOUSEBUTTONNAMES = {1:'left',2:'middle',3:'right',4:'mouse wheel up',5:'mouse wheel down'}
class MouseWidgetClick(ResponseCollector):
    """Records mouse clicks on specific areas of the screen.
    
    possible_resp should be a list of 2-tuples consisting of (button,area) where button is 'left', 'middle', or 'right' and
    area is an EyeScript Shape object or an EyeScript InterestArea object
    """
    def __init__(self,**params):
        ResponseCollector.__init__(self,**params)
        setUpDevice(devices.MouseDevice)
    def handleEvent(self,event):
        if event.type == MOUSEBUTTONDOWN:
#            print "event.pos %s,%s"%(event.pos)
#            print "MOUSEBUTTONNAMES[event.button] %s"%(MOUSEBUTTONNAMES[event.button])
            for button,shape in self['possible_resp']:
                if MOUSEBUTTONNAMES[event.button] == button and shape.contains(event.pos):
                    self['resp'] = (button,shape)
                    self['rt_time'] = event.time
                    self['rt'] = self['rt_time'] - self['onset_time']
                    break
        if event.type == MOUSEBUTTONUP:
            if self['resp'] and self['resp'][0] == MOUSEBUTTONNAMES[event.button] and self['resp'][1].contains(event.pos):
                self['rt_offset_time'] = event.time
                self['rt_offset'] = event.time - self['onset_time']
                self.stop()
                return True
        return False
                    
class MouseDownUp(ResponseCollector):
    def __init__(self,**params):
        ResponseCollector.__init__(self,**params)
        setUpDevice(devices.MouseDevice)
        self.buttonsPressed = []
    def handleEvent(self,event):
        if event.type == MOUSEBUTTONDOWN:
            self.buttonsPressed.append(event.button)
        if event.type == MOUSEBUTTONUP and event.button in self.buttonsPressed and MOUSEBUTTONNAMES[event.button] in self['possible_resp']:
            self.stop()
            return True
        return False

class GazeResponseCollector(ResponseCollector):
    """Abstract class for registering responses consisting of eye movements.
    
    Subclasses register responses under different conditions, e.g.
    when the eyes have fixated on an area and stayed there for a minimum time (ContinuousGaze)
    or as soon as a sample is detected in an interest area (GazeSample).
    New subclasses could be written to handle other cases.
    """
    def __init__(self,**params):
        ResponseCollector.__init__(self,**params)
        setUpDevice(devices.EyeLinkDevice)
    def start(self):
        """Execute operations necessary when response collection is started.
        
        Check if the eyetracker is recording
        Check the eye being recorded from
        Initialize the fixatedArea attribute to None
        """
        ResponseCollector.start(self)
        if not getExperiment().recording:
            raise "Must be recording to monitor gaze position!"
        self.eyeUsed = getTracker().eyeAvailable()
        if self.eyeUsed == 2:    # binocular recording
            self.eyeUsed = getExperiment().params.get('eye_used',1)
        elif self.eyeUsed == -1: # neither eye available!
            raise TrialAbort(pylink.TRIAL_ERROR)
##            getTracker().resetData()
        self.fixatedArea = None

    def respond(self,events):
        """Ensure that handleEvent is always called once whether or not any events have been detected.

        This is necessary because the EyeLinkDevice doesn't post events to EyeScript's event queue, but
        rather, the ContinuousGaze object reads events directly from the EyeLink buffer.

        Maybe someone who is in less of a hurry than I am in right now can replace this with a more elegant solution.
        """
        return ResponseCollector.respond(self,[None])
    
    def handleEvent(self,event):
        if not getExperiment().recording:
            self.stop()
            return False
        if getTracker():        
            action = getTracker().isRecording()
            if action != pylink.TRIAL_OK:
                raise TrialAbort(action)
            return self.checkEyeLink()
        else:
            # So that the experiment can be tested without the eyetracker,
            # just fake a response after 2000 milliseconds.
            if pylink.currentTime() > self['onset_time'] + 2000:
                self['resp'] = self['possible_resp'] and self['possible_resp'][0]
                self['rt'] = 2000
                self['rt_time'] = self['onset_time'] + 2000
                self.stop()
                return True
    def checkEyeLink(self):
        """Check the data from the EyeLink to see whether the conditions have been met for registering a response.
        If so, record rt, rt_time, and resp, and return True; otherwise return False.
        This method is filled in by the child classes.
        """
        pass

class GazeSample(GazeResponseCollector):
    """Monitor subject's gaze and check if it falls in a given area.
    
    Return a response as soon as a sample in an interest area is detected (don't wait for a fixation to be detected).
    """
    def checkEyeLink(self):
        sample = getTracker().getNewestSample()
        sampledata = sample and (
                (self.eyeUsed == 1 and sample.isRightSample() and sample.getRightEye()) or
                (self.eyeUsed == 0 and sample.isLeftSample() and sample.getLeftEye())
                )
        if sampledata:
            for area in self['possible_resp']:
                if area.contains(sampledata.getGaze()):
                    self.params['rt_time'] = sample.getTime()
                    self.params['rt'] = sample.getTime() - self.params['onset_time']
                    self.params['resp'] = area
                    # TODO: Test the following code:
                    # In particular: is the number specifying the offset
                    # between here and the eye tracker meaningful and
                    # correct?  What's the meaning of this number anyway?
                    # And what's it used for?
                    getTracker().sendMessage("%s.END_RT"%(self['name']))
                    #getTracker().sendMessage("%d %s.END_RT"%(self['rt_time']-pylink.currentTime(),
                    #                                         self['name']))
                    self.stop()
                    return True
        return False
                    
                

class ContinuousGaze(GazeResponseCollector):
    """Monitor subject's fixations and check if they fall in a given area and stay there continuously for a minimum duration
    
    Specifically, the ContinuousGaze object registers a response when the eyetracker has detected a fixation within a given
    interest area, AND when the eyes have stayed within that area continuously for a specified length of time.
    
    The ContinuousGaze object will stop response collection as soon as the first such response is detected.
    
    Parameters (can be set as a keyword when the Gaze object is first created, in addition to the ResponseCollector parameters):
    possible_resp:  a list of Shape or InterestArea object specifying areas of the screen to monitor
    min_fixation:  time the subject has to remain fixated in an interest area before it counts as a response
                   (0 --> register a response as soon as a fixation in an interest area is detected).
    """
    def checkEyeLink(self):
        """Check if the eyes have fixated in one of the areas listed in possible_resp, and have stayed there for the specified minimum time.
        If so, record rt, rt_time, and resp, and return True; otherwise return False.
        """   
            
        if self.fixatedArea: #We've already started fixating on one of the areas in possible_resp
            sample = getTracker().getNewestSample()
            # Retrieve the sample data from whichever eye we care about
            sampledata = sample and (
                (self.eyeUsed == 1 and sample.isRightSample() and sample.getRightEye()) or
                (self.eyeUsed == 0 and sample.isLeftSample() and sample.getLeftEye())
                )
            if sampledata:
                if self.fixatedArea.contains(sampledata.getGaze()):
                    # Check whether they've stayed in the interest area for the specified minimum time
                    if sample.getTime() - self.fixtime > self.params['min_fixation']:
                        self.params['rt_time'] = self.fixtime
                        self.params['rt'] = self.params['rt_time'] - self.params['onset_time']
                        self.params['resp'] = self.fixatedArea
                        # TODO: Test the following code:
                        # In particular: is the number specifying the offset
                        # between here and the eye tracker meaningful and
                        # correct?  What's the meaning of this number anyway?
                        # And what's it used for?
                        getTracker().sendMessage("%s.END_RT" % self['name'])
                        self.stop()
                        return True
                else: # The eye has left the interest area.  
                    self.fixatedArea = None
                    
              
        else:
            # Check whether we have a fixation in one of the areas in possible_resp
            eventType = getTracker().getNextData()
            if eventType == pylink.STARTFIX or eventType == pylink.FIXUPDATE or eventType == pylink.ENDFIX:
                event = getTracker().getFloatData()
    ##                        print "event.getEye(): %d"%(event.getEye())
    ##                        print "event.getStartGaze(): (%d,%d)"%event.getStartGaze()
                if event.getType() == pylink.STARTFIX and event.getEye() == self.eyeUsed:
                    for area in self.params['possible_resp']:
                        if area.contains(event.getStartGaze()):
                            self.fixtime=event.getStartTime()
                            self.fixatedArea = area
                            break
                if (event.getType() == pylink.FIXUPDATE or event.getType() == pylink.ENDFIX) and event.getEye() == self.eyeUsed:
                    for area in self.params['possible_resp']:
                        if area.contains(event.getAverageGaze()):
                            self.fixtime=event.getStartTime()
                            self.fixatedArea = area
                            break
        return False
        



BBOXMAPPING = {0:4,6:3,5:2,2:1,1:5,4:6,3:7,7:8}
def byteToKey(byte):
    """Convert byte input from a Cedrus button box to the number of the button box key specified by the byte
    """
    return (BBOXMAPPING[ord(byte)/32],(ord(byte)/16)%2)
def bytesToRT(bytes):
    """Convert byte input from a Cedrus device to an integer representing response time
    """
    return (256^3)*ord(bytes[3])+(256^2)*ord(bytes[2])+256*ord(bytes[1])+ord(bytes[0])
      

class CedrusButtons(ResponseCollector):
    """Collect responses from a Cedrus button box
    """
    def __init__(self,**params):
        ResponseCollector.__init__(self,**params)
        self.bbox = getDevice("CedrusButtonsDevice")

    def handleEvent(self,event):
        if event.type == CEDRUS_BUTTON_DOWN and event.key in self['possible_resp'] or "any" in self['possible_resp']:
            self['rt'] = event.time-self['onset_time']
            self['rt_time'] = event.time
            self['resp'] = event.key            
            getTracker().sendMessage("%d %s.END_RT"%(self['rt_time']-pylink.currentTime(),self['name']))
            return True
        elif event.type == CEDRUS_BUTTON_UP and event.key == self['resp']:
            self['rt_offset'] = event.time - self['onset_time']
            self['rt_offset_time'] = event.time
            getTracker().sendMessage("%d %s.offset"%(self['rt_offset_time']-pylink.currentTime(),self['name']))
            self.stop()
            return False

class Speech(ResponseCollector):
    """Collects spoken responses using Microsoft speech recognition
    """


    def __init__(self,**params):
        """Add the possible responses to the words that Microsoft Speech Recognition will consider as candidates
        """
        ResponseCollector.__init__(self,**params)
        getDevice(devices.SpeechDevice).addWords(self['possible_resp'])
        if self.get('cresp',False): self['cresp'] = self['cresp'].capitalize()
        self['possible_resp'] = [resp.capitalize() for resp in self['possible_resp']]
    
    def handleEvent(self,event):
        """Check if the speech recognition detected a word in possible_resp
        """
        if event.type == SPEECH_RECOGNITION:
            if event.word in self['possible_resp']:
                self['rt_time'] = event.time
                getTracker().sendMessage("%d %s.END_RT"%(event.time-pylink.currentTime(),self['name']))
                self['resp'] = event.word
                self['rt'] = event.time - self['onset_time']
                return True
        return False
        
