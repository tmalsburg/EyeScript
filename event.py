"""EyeScript scripts will normally not need to directly deal with events, but will work through ResponseCollector objects instead.
"""

class ESevent:
    """
    Wrapper class for pygame events, to allow events to be timestamped as soon as they're detected.
    
    ESevents are returned by the poll method of device objects.
    Unlike pygame events, ESevents can have arbitrary attributes defined for them (e.g. a widget attribute, for a mouse-down event)
    Pygame events are documented at www.pygame.org.  Pygame events hold the data associated with individual mouse downs, mouse ups, mouse motions, key downs, key ups,
    and potentially, user-defined events such as speech responses.
    """
    def __init__(self,pygameEvent,time=None):
        """
        Store the pygame event and record the time (defaults to current time when __init__ is run)
        """
        if time == None: self.time = pylink.currentTime()
        else: self.time = time
        self.pygameEvent = pygameEvent
    def __getattr__(self,attribute):
        """
        The esEvent will have all the attributes as the pygame event it contains.
        """
        return getattr(self.pygameEvent,attribute)
            
