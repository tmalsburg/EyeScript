# -*- coding: utf-8 -*-
"""Defines the abstract Trial class from which all trial definitions inherit. Also defines functions that may be called within a trial for eyetracker communication.
"""
from experiment import getTracker, getExperiment, getLog, calibrateTracker,checkForResponse,TrialAbort,Error
import pygame,pylink
from math import pi, sin, cos
from VisionEgg.FlowControl import Presentation, Controller, FunctionController
from VisionEgg.Core import *
import random
import VisionEgg.GL as gl

class Trial:
    """Abstract class for running a trial and communicating with the eyetracker.

    Attributes:
    The following are optional attributes which may be set in the __init__ method of child classes.
    dataViewerBG: Display object showing the image to be displayed in the Data Viewer for this trial 
    rtPeriod: 2-tuple that sets the endpoints of the RT period for the Data Viewer.
              If dataViewerBG is set, rtPeriod defaults to the onset and end of the dataViewerBG display.
    metadata: dictionary containing trial metadata to be logged in the text log file and in the eyetracker data file
    """
    trialNumber = 0
    bgNumber = 0
    def __init__(self,stim):
        """Pre-loads stimuli and sets the trial's attributes. Defined in child classes.
        """
        pass
    
    def setMetadata(self,md):
        self.metadata = md
        
    def record(self,*args,**keywords):
        """Runs the trial displays while communicating with the eyetracker.

        TO-DO:  currently contains a hack for stopping audio when trial is aborted.
        This needs to be done in a more general and implementation-independent way.
        """
        while 1:            
            getTracker().flushKeybuttons(1)
            Trial.trialNumber += 1
            getLog().push()
            getLog().logAttributes(trialNumber=Trial.trialNumber)
            getLog().logAttributes(getattr(self,'metadata',{}))
            getTracker().sendMessage('TRIALID %s'%(Trial.trialNumber))
            getTracker().drawText("Trial_%s\n"%(Trial.trialNumber),pos=(1,20))
            getTracker().sendCommand("record_status_message 'TRIALID %s'"%(Trial.trialNumber))
            self.sendDataViewerBG()
            self.sendRTperiod()
            try:
                result = self.run(*args,**keywords)
            except TrialAbort,abort:
                
                for rc in getExperiment().response_collectors: rc.stop()

                # HACK!!!
                # Need to find a good implementation-independent way of ensuring that sound streams get stopped.
                pygame.mixer.stop()
                
                getExperiment().recording = False
                pylink.endRealTimeMode()
                getLog().logAttributes(trial_abort=abort.abortAction)
                for key,value in getLog().currentData().iteritems():
                    setTrialVar(key,value)
                    pygame.time.delay(1)
                getLog().pop()
                getTracker().sendMessage('TRIAL_RESULT %d'%(abort.abortAction))
                if abort.abortAction == pylink.REPEAT_TRIAL:
                    pass
                elif abort.abortAction == pylink.TRIAL_ERROR:
                    calibrateTracker()
                elif abort.abortAction == pylink.SKIP_TRIAL:
                    return None
                else:
                    raise
            else:
                getLog().logAttributes(trial_abort=0)
                for key,value in getLog().currentData().iteritems():
                    setTrialVar(key,value)
                    pygame.time.delay(1)
                getLog().pop()
                getTracker().sendMessage('TRIAL_RESULT 0')
                return result

    def run(self,*args,**keywords):
        """Defines what a subject will see and do during a trial. Defined in the child classes.
        """
        pass
    
    def setDataViewerBG(self,display,screen_image_file = None,interest_area_file = None):
        self.dataViewerBG = display
        self.bgImageFile = screen_image_file or os.path.join(getExperiment()['data_file_root_name']+"_screenimages","image_%s%sjpg"%(Trial.bgNumber,os.extsep))
        self.bgIAfile = interest_area_file or os.path.join(getExperiment()['data_file_root_name']+"_interest_areas","image_%s%sias"%(Trial.bgNumber,os.extsep))
        display.write_screen_image_file(os.path.join(getExperiment()['data_directory'],self.bgImageFile))
        display.write_interest_area_file(os.path.join(getExperiment()['data_directory'],self.bgIAfile))
        Trial.bgNumber += 1

    def sendDataViewerBG(self):
        """Lets the Data Viewer know the names of the files containing the background image and the interest area definitions
        """
        if hasattr(self,'dataViewerBG'):
            if self.dataViewerBG.params.get('screen_image_file',False):
                pygame.time.delay(2)
                getTracker().sendMessage("!V IMGLOAD FILL %s"%self.dataViewerBG['screen_image_file'])
            if self.dataViewerBG.get('interest_area_file',False):
                pygame.time.delay(2)
                getTracker().sendMessage("!V IAREA FILE %s"%self.dataViewerBG['interest_area_file'])

    def sendRTperiod(self):
        """Lets the Data Viewer know the endpoints of the RT period, so data outside that period can easily be filtered out
        """
        if not hasattr(self,'rtPeriod'):
            if hasattr(self,'dataViewerBG') and len(self.dataViewerBG['response_collectors']) > 0:
                self.rtPeriod = ("%s.SYNCTIME"%(self.dataViewerBG['name']),"%s.END_RT"%(self.dataViewerBG['response_collectors'][0]['name']))
            else:
                return
        
        getTracker().sendMessage("!V V_CRT MESSAGE %s %s"%(self.rtPeriod))

class PupilCalibrationTrial(Trial):
    def __init__(self,pattern="continuous",color=None,bgcolor=None):
        self.metadata = {"experiment":"pupil_calibration","pattern":pattern}
        self.pattern = pattern
        self.color = color or getExperiment()['color']
        self.bgcolor = bgcolor or getExperiment()['bgcolor']
        self.target = VisionEgg.MoreStimuli.Target2D(size=(6.0,6.0),color = self.color)
        self.targetVP = VisionEgg.Core.Viewport(screen=getExperiment().screen,stimuli=[self.target])
        self.rtPeriod = ("END_FILLER","END_RT")
    def run(self):
        startRecording()
        starttime = pylink.currentTime()
        getExperiment().screen.parameters.bgcolor = self.bgcolor
        getTracker().sendMessage("SYNCTIME")
        if self.pattern == "continuous":
            iteration = 0
            filler = False
            while iteration <= 1.25:
                if filler == False and iteration >= 0.25:
                    # This is point where we're actually going to use the data
                    # Before this was just to get the subject warmed up
                    filler = True
                    getTracker().sendMessage("END_FILLER")
                checkForResponse()
                t = (pylink.currentTime() - starttime) * 0.00012
                t = t - sin(8*t)/64
                iteration = t / (2*pi)
                getExperiment().eyelinkGraphics.draw_cal_target(getExperiment()['screen_size'][0]/2 + 153*sin(t) + 204*sin(9*t),getExperiment()['screen_size'][1]/2 + 153*cos(t) + 204*cos(9*t))
                
        elif self.pattern == "discrete":
            getExperiment().eyelinkGraphics.setCalibrationColors(self.color,self.bgcolor)
            targets = []
            for i in range(3):
                for j in range(3):
                    targets.append([(i+0.5)*getExperiment()['screen_size'][0]/3,(j+0.5)*getExperiment()['screen_size'][1]/3])
            for i in range(1,3):
                for j in range(1,3):
                    targets.append([i*getExperiment()['screen_size'][0]/3,j*getExperiment()['screen_size'][1]/3])
            random.shuffle(targets)
            targets.append(targets[0]) # Redo the first fixation point at the end so we can discard the first one
            for i,target in enumerate(targets):
                if i == 1: getTracker().sendMessage("END_FILLER")
                getExperiment().eyelinkGraphics.draw_cal_target(*target)

                starttime = pylink.currentTime()
                while pylink.currentTime() < 1500+starttime: checkForResponse()
        else:
            raise "PupilCalibrationTrial:  bad argument to pattern: %s"%self.pattern

        getTracker().sendMessage("END_RT")
        stopRecording()
 
def startRecording():
    """Commence eyetracker recording and verify that it's working.
    """
    getTracker().resetData()
    getTracker().startRecording(1,1,1,1)
    getExperiment().recording = True
    pylink.beginRealTimeMode(100)
    try:
        if not getTracker().waitForBlockStart(1000,1,1):
            raise Exception("waitForBlockStart failed")
    except Exception:
        getTracker().drawText("LINK DATA NOT RECEIVED!",pos=(1,20))
        pylink.endRealTimeMode()
        pylink.msecDelay(2000)
        getTracker().stopRecording()
        print "LINK DATA NOT RECEIVED!"
        raise TrialAbort(pylink.TRIAL_ERROR)

def stopRecording():
    """Stop eyetracker recording
    """
    if getExperiment().recording:
        pylink.endRealTimeMode()
        pylink.msecDelay(100)
        getTracker().stopRecording()
        getExperiment().recording = False

def driftCorrect(color=None,bgcolor=None,target=None):
    """Draw a target and perform drift correction

    Arguments:
    color:  An RGB 3-tuple specifying the foreground color for the drift correction screen.
            Default is the experiment 'color' parameter
            E.g. color = (0,0,0) is black, color = (1,1,1) is white.
    bgcolor:  An RGB 3-tuple specifying the background color.  Default is the experiment 'bgcolor' parameter
    target:  A 2-tuple (x,y) specifying the coordinates of the fixation target to be displayed.
             Default is the center of the screen
    """
    if getExperiment().recording: raise EyetrackerError("Attempt to drift correct while recording in progress")
    # If no target is specified, the target is the center of the screen
    target = target or (getExperiment().params['screen_size'][0]/2,getExperiment().params['screen_size'][1]/2)
    color = color or getExperiment().params['color']
    bgcolor = bgcolor or getExperiment().params['bgcolor']
    getExperiment().eyelinkGraphics.setCalibrationColors(color,bgcolor)
    mouseVisibility = pygame.mouse.set_visible(False)
    while 1:
        try:
            error=getTracker().doDriftCorrect(target[0],target[1],1,1)
            if error == 27:
                calibrateTracker((color,bgcolor))
            else:
                print "drift correct error %s"%error
                break
        except RuntimeError:
            pass
    pygame.mouse.set_visible(mouseVisibility)
        
def gcFixation(target=None,color=None,bgcolor=None,duration=None,buffer_size=None):
    """Displays a fixation point and waits until the subject has fixated on it for a minimum duration.

    The Eyetracker
    """
    if buffer_size == None:  buffer_size = getExperiment()['gcbuffer_size']
    if not getExperiment().recording:
        raise EyetrackerError("Must be recording when gcFixation is called!")
    target = target or getExperiment().params.get('fixation_target',(
        getExperiment().params['screen_size'][0]/2,getExperiment().params['screen_size'][1]/2
        )
                                                     )
    color = color or getExperiment().params['color']
    bgcolor = bgcolor or getExperiment().params['bgcolor']
    duration = duration or getExperiment().params.get('min_fixation',800)
    getExperiment().eyelinkGraphics.setCalibrationColors(color,bgcolor)
    getExperiment().eyelinkGraphics.draw_cal_target(target[0],target[1])
    if getTracker():
        eyeUsed = getTracker().eyeAvailable()
        if eyeUsed == 2:    # binocular recording
            eyeUsed = getExperiment().params.get('eye_used',1)
        elif eyeUsed == -1: # neither eye available!
            raise TrialAbort(pylink.TRIAL_ERROR)
        getTracker().resetData()
##        getTracker().sendCommand("clear_cross %d %d %d"%(target[0],target[1],15))
        fixarea = pygame.Rect(target[0]-buffer_size,
                              target[1]-buffer_size,
                              2*buffer_size,
                              2*buffer_size
                              )
        infixarea = False
        while 1:
            action = getTracker().isRecording()
            if action != pylink.TRIAL_OK:
                raise TrialAbort(action)
                
            
            if infixarea:
                sample = getTracker().getNewestSample()
                sampledata = sample and (
                    (eyeUsed == 1 and sample.isRightSample() and sample.getRightEye()) or
                    (eyeUsed == 0 and sample.isLeftSample() and sample.getLeftEye()) or
                    False
                    )
                if sampledata:
                    if fixarea.collidepoint(sampledata.getGaze()):
                        if sample.getTime() - fixtime > duration:
                            break
                    else:
                        infixarea = False
                        getTracker().resetData()
                        
                  
            else:
                eventType = getTracker().getNextData()
                if eventType == pylink.STARTFIX or eventType == pylink.FIXUPDATE or eventType == pylink.ENDFIX:
##                        print "Fixation started"
                    event = getTracker().getFloatData()
##                        print "event.getEye(): %d"%(event.getEye())
##                        print "event.getStartGaze(): (%d,%d)"%event.getStartGaze()
                    if ((event.getType() == pylink.STARTFIX and
                         event.getEye() == eyeUsed
                         and fixarea.collidepoint(event.getStartGaze())) or
                        ((event.getType() == pylink.FIXUPDATE or event.getType() == pylink.ENDFIX) and
                         event.getEye() == eyeUsed
                         and fixarea.collidepoint(event.getAverageGaze()))):
##                            print "Fixation in critical area!"
                        fixtime = event.getStartTime()
                        infixarea = True
    else:
        pygame.time.delay(duration)
    getExperiment().eyelinkGraphics.erase_cal_target()

def gcFlashFixation(target=None, color=None, bgcolor=None, duration=400, delay=100,
                    buffer_size=None, nflashes=6):

   for i in range(0, nflashes):
       gcFixation(target, color, bgcolor, duration, buffer_size)
       pygame.time.delay(delay)
     
  

def setTrialVar(varName,value):
    """Sets the value of a trial variable, to inform the Data Viewer about trial metadata
    """
    getTracker().sendMessage("!V TRIAL_VAR %s %s"%(varName,value))

class EyetrackerError(Error):
    pass


