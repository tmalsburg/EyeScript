# -*- coding: utf-8 -*-
class InterestArea:
    """
    Represents a region of the screen, for eye data reporting purposes.
    
    The EyeLink Data Viewer can associate fixations with regions on the screen, for instance the regions around each word in a sentence.
    An InterestArea object stores the information for a region for writing in the data file to be read by the Data Viewer.
    
    Attributes:
    shape -- an EyeScript shape object defining the extent of the Interest Area
    label -- string to label the interest area, to identify it for the Data Viewer
    """
    def __init__(self,shape,label=""):
        """Arguments: the interest area's shape and label
        """
        self.label = label
        self.shape = shape
    def __str__(self):
        """Return a string representation of the interest area for printing in a data file
        
        The string representation will be the label, or if a label was not specified, the shape name concatenated with the shape coordinates
        """
        return str(self.label) or str(self.shape)
    def coordinateString(self):
        """Used by display class methods that record the display's interest areas.
        
        Returns a string representation of the interest area coordinates for printing in a .ias file readable by the EyeLink Data Viewer
        """
        return "%s\t%s\t%s\t%s"%(self.shape.rect.left,self.shape.rect.top,self.shape.rect.right,self.shape.rect.bottom)
    
    def shapeName(self):
        """Used by display class methods that record the display's interest areas.
        
        Return the name of the shape for recording in the interest area file, so that the data viewer can handle the interest area appropriately.
        
        Currently the data viewer recognizes the shapes RECTANGLE, ELLIPSE and FREEHAND.
        """
        return self.shape.__class__.__name__.upper()
    
    def contains(self,point):
        """
        Return True or False depending on whether this interest area contains the given point (specified as an (x,y) tuple).
        """
        return self.shape.contains(point)
