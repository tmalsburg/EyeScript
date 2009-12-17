"""This module defines the Experiment class for high-level control of the experiment.

It also contains classes and functions for data logging, as well as a few useful utility functions.
"""

import pylink
from pylink.EyeLinkCoreGraphics.EyeLinkCoreGraphicsVE import EyeLinkCoreGraphicsVE
import VisionEgg.Core
import os
import pygame
from UserDict import DictMixin


class Experiment(DictMixin):
    """Contains methods for setting up and running an experiment.
    
    In an EyeScript script, after EyeScript is imported but before any EyeScript functions are used, you must set up an experiment object.
    The __init__ method of Experiment takes keyword arguments specifying the parameters for the experiment.  Any keywords not set here
    will default to the values in defaults.py.  See defaults.py for descriptions of all possible parameters.
    
    Example:
    Experiment(screen_size = (1600,1200), align=('left','center'),margins=[20,0,20,0],font_size=24,font_name='courbd.ttf',session_info=['session','list_number'])
    
    The optional session_info keyword above is used to specify session data (in addition to subject number) that the experimenter will be asked to enter at runtime.
    
    Once the experiment object is created, you can access it using the getExperiment function.
    The experiment object's parameters (including those entered by the experimenter at run-time) can be accessed using dictionary notation, e.g.
    
    getExperiment()['subject']
    getExperiment()['session']
    getExperiment()['list_number']
    """
    theExperiment = None
    def __init__(self,**params):
        """Sets the experiment's parameters and attributes, and sets up VisionEgg, the eyetracker, and the EventLog.

        Optionally takes keyword arguments which set the experiment's parameters, overriding the values in defaults.py
        """
        Experiment.theExperiment = self
        
        from defaults import defaultParams
        unusedKeys = [str(key) for key in params.keys() if key not in defaultParams.keys()]
        if unusedKeys: raise "Experiment():  Experimental parameter(s) not recognized: %s"%(", ".join(unusedKeys))
        self.params = defaultParams.copy()
        self.update(params)
        
        #Read in the subject ID and set the data filename accordingly
        if not os.path.isdir(self['data_directory']):
            os.mkdir(self['data_directory'])
            
        while 1:
            subjectString = self['subject'] = raw_input("Enter subject ID (0 for no data logging): ")
            if self['subject'].isdigit():
                self['subject'] = int(self['subject'])
                subjectString = "%03d"%self['subject']
            for attribute in self['session_info']:
                self[attribute] = raw_input("Enter %s: "%attribute)
                if self[attribute].isdigit(): self[attribute] = int(self[attribute])
            
            sessionsuffix = 'session' in self['session_info'] and "_%s"%self['session'] or ""
            self['data_file_root_name'] = self['data_filename_prefix']+subjectString+sessionsuffix
            self.eyedatafile=os.path.join(self['data_directory'],"%s%sedf"%(
                self['data_file_root_name'],os.extsep
                )
                                              )
            self.edffile="%s%s%s%sedf"%(
                self['edf_prefix'],subjectString,sessionsuffix[1:],os.extsep
                )
            self.textdatafile=os.path.join(self['data_directory'],"%s%stxt"%(
                self['data_file_root_name'],os.extsep
                )
                                      )
            print "\nPlease verify the session info."
            for attribute in ['subject'] + self['session_info']: print "%s: %s"%(attribute,self[attribute])
            if self['subject'] > 0 and (os.path.isfile(self.eyedatafile) or os.path.isfile(self.textdatafile)):
               print "WARNING: data file already exists and will be overwritten unless the session info is changed."
            if raw_input("\nKeep the session info as is? (y/n): ")=="y": break

        
        self.log = self.EventLog(**dict([(attribute,self[attribute]) for attribute in ['subject']+self['session_info']]))

        from EyeScript import __version__
        self.log.logAttributes(EyeScript_version = __version__)

        self.trialNumber = 0
        self.recording = False
        
        self._vEggConfig()
        self.screen = VisionEgg.Core.get_default_screen()  
        self._trackerCreate()
        pygame.event.set_allowed(None) # If/when mouse and keyboard devices are created, then mouse and keyboard events will be allowed
        self.devices = []
        self.response_collectors = []
        self.streams = []
        import devices
        setUpDevice(devices.KeyboardDevice) #Set up the keyboard so that we can (at least) handle the abort key combo during the experiment.
        from displays import TextDisplay
        # Show a display while we're setting up the trials.
        self.eventQueue = []
        TextDisplay("Loading experiment...",duration=0,response_collectors=[]).run()
    
    def _vEggConfig(self):
      """Helper method not directly called in EyeScript scripts in general
      
      Configures VisionEgg, refer to VisionEgg docs
      """
      # start logging
      VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

      VisionEgg.config.VISIONEGG_GUI_INIT = 0
      VisionEgg.config.VISIONEGG_FRAMELESS_WINDOW = 1
      VisionEgg.config.VISIONEGG_FULLSCREEN = 1
      VisionEgg.config.VISIONEGG_HIDE_MOUSE = True
      VisionEgg.config.VISIONEGG_MONITOR_REFRESH_HZ = self['refresh_rate']
      VisionEgg.config.VISIONEGG_SCREEN_W = self['screen_size'][0]
      VisionEgg.config.VISIONEGG_SCREEN_H = self['screen_size'][1]
      VisionEgg.config.VISIONEGG_PREFERRED_BPP = self['bits_per_pixel']

    def _trackerCreate(self):
        """Helper method not directly called in EyeScript scripts in general
        
        configures the Eyelink eyetracker
        """        
        try:
            self.tracker = pylink.EyeLink()
        except (RuntimeError,AttributeError):
            self.tracker = EyetrackerStub()

        #This tells the tracker to use VisionEgg to display Eyelink graphics
        #including calibration points, camera images, etc.
        self.eyelinkGraphics = EyeLinkCoreGraphicsVE(self.screen,self.tracker)
        pylink.openGraphicsEx(self.eyelinkGraphics)
        self.eyelinkGraphics.setCalibrationColors(self['color'],self['bgcolor'])

        for key,value in self.iteritems():
            command = key.split('_',1)
            if len(command) > 1 and command[0] == 'tracker':
                getattr(self.tracker,command[1])(value)
                
        if self['heuristic_filter'] == 'off': self.tracker.setHeuristicFilterOff()
        else: self.tracker.setHeuristicFilterOn()
         
        #Set whether beeps should be played during drift correction
        pylink.setDriftCorrectSounds(*self['setDriftCorrectSounds'])
      
        # open the datafile on the operator pc
        if self['subject'] > 0: self.tracker.openDataFile(self.edffile)
        
        self.tracker.sendCommand("screen_pixel_coords =  0 0 %d %d"%(self['screen_size']))



    def close(self):
        """Helper method not directly called in EyeScript scripts in general
        
        Shuts down VisionEgg and writes the EventLog to a file."""
        self.tracker.setOfflineMode()
        if self['subject'] > 0:            
            self.log.writeLog(self.textdatafile)
            pylink.msecDelay(500)
            try:
                self.tracker.closeDataFile()
                self.tracker.receiveDataFile(self.edffile,self.eyedatafile)
            except RuntimeError:
                pass
        self.tracker.close()
        self.screen.close()

    def __getitem__(self,name):
        """Helper method not directly called in EyeScript scripts
        
        Allows the experiment's parameters to be accessed using dictionary notation
        """
        return self.params[name]

    def __setitem__(self,name,value):
        """Helper method not directly called in EyeScript scripts
        
        Allows the experiment's parameters to be accessed using dictionary notation
        """
        self.params[name]=value

    def keys(self):
        """Helper method not directly called in EyeScript scripts
        
        Allows the experiment's parameters to be accessed using dictionary notation
        """
        return self.params.keys()

    class EventLog:
        """Records data, and associated metadata, from an experimental session.

        Attributes:
        data:  a list of the data points recorded during the experiment.  Each data point is a leaf LogNode object.
        currentNode:  a LogNode representing the current session, block, trial, or ScriptStep for which we're logging data
        """
        def __init__(self,**attributes):
            """Sets the object's attributes and optionally does some top-level logging.

            Arguments:  filename, the name of the file to which the data will be written.
            Any additional keyword arguments are recorded as top-level metadata (e.g. subject and session number)."""
            self.data = []
            self.currentNode = self.LogNode({},attributes)

        def currentData(self):
            return self.currentNode
            
        def logAttributes(self,**attributes):
            """Records metadata associated with the current session, block, trial, or ScriptStep.

            This metadata is included in all events logged during this session/block/trial/ScriptStep.
            
            logAttributes is called with keyword arguments specifying the attributes to be logged and their values.
            """
            self.currentNode.update(attributes)
        def push(self,**attributes):
            """Lets the EventLog know that the experiment is entering a new block, trial, or ScriptStep.

            push may optionally be called with keyword arguments defining metadata to be logged at the new level."""
            newNode = self.LogNode(self.currentNode,attributes)
            self.currentNode.children.append(newNode)
            self.currentNode = newNode
            
        def pop(self):
            """Lets the EventLog know that the experiment has exited a block, trial, or ScriptStep."""
            self.currentNode = self.currentNode.parent
            
        def logEvent(self,**attributes):
            """Add a line to the output log file with the given attributes
            """
            self.push(**attributes)
            self.pop()

        def writeLog(self,textdatafile):
            """Writes all data to a text file.

            Argument:  textdatafile, the name of the file to which the data will be written.
            """
            # Get to the top-level node
            while self.currentNode.parent: self.pop()

            # Write the header of the data file, containing the names of the attributes whose values will be written
            self.headings = []
            data = []

            def logChildren(node):
                if node.children:
                    for child in node.children: logChildren(child)
                else: # This is a leaf node.
                    for key in node.keys():
                        if not (key in self.headings): self.headings.append(key)
                    data.append(node)

            logChildren(self.currentNode)
            
            logfile = open(textdatafile,'w')
            self.writeEvents(data,logfile)
            logfile.close()

        def writeEvents(self,data,logfile):
            # Write the column headings, containing the attribute names
            logfile.write("\t".join(self.headings)+"\n")

            # Write the data
            for event in data:
                logfile.write("\t".join([str(event.get(heading,getExperiment()['NA_string'])) for heading in self.headings]))
                logfile.write('\n')


        class LogNode(DictMixin,dict):
            """LogNode maps attribute names to attribute values.

            LogNodes are used by the EventLog to hold data at the session, block, trial, ScriptStep, and event levels.
            Each LogNode inherits the attributes of its parent.
            The LogNode class inherits from dict, and the attribute values are set and retrieved using dictionary syntax.
            """
            def __init__(self,parent={},attributes={}):
                self.parent = parent
                self.update(attributes)
                self.children = []

            def __getitem__(self,key):
                if dict.has_key(self,key):
                    return dict.__getitem__(self,key)
                else:
                    return self.parent[key]
            def keys(self):
                mykeys = dict.keys(self)
                mykeys.sort()
                return self.parent.keys()+mykeys

def checkForResponse():
    """Check for subject responses and experimenter-initiated abort.
    
    Returns:  list of ResponseCollector objects (if any) that received a response
    
    This function is repeatedly called by the run method of display objects, to check for responses while the display is running.
    In most EyeScript scripts, it is sufficient to use the displays' run methods rather than directly calling checkForResponse.
    checkForResponse should be called (repeatedly) whenever the experiment does any waiting or looping that's not a display's run method (example: a loop
    that waits for the subject's gaze to fall on a critical region before playing a beep). Besides making sure any responses are logged accurately,
    checkForResponse is also necessary to check for experimenter-initiated aborts and to maintain contact with the operating system.
    """
    events = getEvents()
    return [rc for rc in getExperiment().response_collectors if rc.respond(events)]

def updateEvents():
    if getExperiment().recording:
        action = getTracker().isRecording()
        if action != pylink.TRIAL_OK:
            raise TrialAbort(action)
    pygame.event.pump()
    for device in getExperiment().devices: getExperiment().eventQueue.extend(device.poll())

def getEvents():
    updateEvents()
    events = getExperiment().eventQueue
    getExperiment().eventQueue = []
    return events

def getDevice(device_class):
    """Given a class, return the device object from the experiment's list devices that matches that class, or None if the device hasn't been added yet
    """
    for device in getExperiment().devices:
        if device.__class__ == device_class: return device
    else:
        return None

def setUpDevice(device_class):
    """Given a device class, adds a device of that class to the experiment's list of devices (if it's not already added).
    """
    if not getDevice(device_class): getExperiment().devices.append(device_class())

class TrialAbort(Exception):
    """Exception raised if the experimenter aborts a trial via CTRL-ALT-A on the EyeLink PC, or if there's an error with the eyetracker.
    """
    def __init__(self,abortAction):
        self.abortAction = abortAction
    def __str__(self):
        if self.abortAction == pylink.REPEAT_TRIAL:
            return "Repeat trial"
        elif self.abortAction == pylink.SKIP_TRIAL:
            return "Skip trial"
        elif self.abortAction == pylink.ABORT_EXPT:
            return "Abort experiment"
        elif self.abortAction == pylink.TRIAL_ERROR:
            return "Setup menu"
        elif self.abortAction == 27:
            return "Escape pressed"
        else:
            return self.abortAction

def getExperiment():
    """Returns the last Experiment object created, or None if none has been created yet."""
    return Experiment.theExperiment

def getTracker():
    """Returns an Eyelink object representing the eyetracker, or a stub object if the tracker isn't connected."""
    return getExperiment().tracker

def getLog():
    """Returns the EventLog object for logging experimental data."""
    return getExperiment().log

def calibrateTracker(colors=None):
    """Tells the eyetracker PC to go to the setup menu

    The colors argument is a 2-tuple defining the foreground and background colors for the calibration display as RGB 3-tuples
    """
    if colors: getExperiment().eyelinkGraphics.setCalibrationColors(colors[0],colors[1])
    mouseVisibility = pygame.mouse.set_visible(False)
    print 'setting up tracker %s'%(getTracker() or 'Tracker is fake')
    getTracker().doTrackerSetup(getExperiment()['screen_size'][0],getExperiment()['screen_size'][1])
    pygame.mouse.set_visible(mouseVisibility)

def runSession(callback):
    """Calls the given function, in addition to doing some logging and final cleanup.

    runSession returns the value of the argument function (possibly None).

    Argument: callback, the function defining what happens during a session.
    """
    from displays import TextDisplay
    closeDisplay = TextDisplay("Saving data...",duration=0,response_collectors=[])
    try:
        result=callback()
    finally:
        getExperiment().recording = False
        closeDisplay.run()
        getExperiment().close()
    return result
    
class EyetrackerStub:
    """If the eyetracker is not connected, then an object of this class is used in place of a real tracker.
    """
    def __init__(self): pass
    
    def __getattr__(self,name):
        """Called if a method is not defined in this class.

        Has the effect of replacing all the EyeLink methods with stubs, except those defined in this class.
        """
        return lambda *args,**kw: 1

    def __nonzero__(self):
        """Asserts that an EyetrackerStub object is considered False for the purposes of truth-value testing.
        """
        return False
    
    def readKeyButton(self):
        return (0,0,0,0,0)

    def doDriftCorrect(targetX,targetY,*args):
        pass
#        print "about to draw cal target"
#        getExperiment().eyelinkGraphics.draw_cal_target(targetX,targetY)
#        print "about to delay"
#        pygame.time.delay(1500)
#        print "about to erase cal target"
#        getExperiment().eyelinkGraphics.erase_cal_target()
#        print "doDriftCorrect done"

    def isRecording(self):
        return pylink.TRIAL_OK

    def beginRealTimeMode(self,delay):
        pygame.time.delay(delay)

    def eyeAvailable(self):
        return 2



def formatMoney(amount):
    """Takes a money amount as a float, positive or negative, in dollars; returns the amount as a formatted string"""
    if amount<0:
        return "-$%0.2f"%(-round(amount,2))
    else:
        return "$%0.2f"%round(amount,2)

class Error(Exception):
    pass


    
