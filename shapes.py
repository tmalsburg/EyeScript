# -*- coding: utf-8 -*-
"""Contains classes defining screen regions.  Such regions may be used to define interest areas for the Data Viewer, or to trigger events in gaze-contingent paradigms.
"""
from pygame import Rect
class Shape:
    """Abstract class representing screen regions, from which shape-specific subclasses will inherit
    
    Attribute:  rect, the bounding rectangle
    """
    def __init__(self, coordinates, name="shape"):
        """Create a shape, given some coordinates.
        
        It may take either
        4 arguments:  left-boundary, top-boundary, width, height, or
        2 arguments, each being a 2-tuple: (left-boundary, top-boundary), (width, height), or
        1 argument: any Python object with a rect attribute, such as another Shape
        (see pygame Rect documentation at http://www.pygame.org/docs/ref/rect.html; the Shape argument(s) are passed directly to Rect)
        """
        self.rect = Rect(*coordinates)
        self.name = name
    
    def __str__(self):
        return "%s_%s"%(self.shapeName(),self.rect)

    def shapeName(self):
        return self.name
    
    def contains(self,point):
        """Returns a boolean specifying whether the interest area contains the point.
        
        Must be defined for each subclass.
        """
        return False
    
    def expand(self,dim,amount):
        """
        Expand the shape in a given direction.
        
        Arguments:
        dim, the direction in which to expand, 'top','left','right', or 'bottom'
        amount, the number of pixels to expand the shape by
        """
        if dim == 'top': self.rect.top -= amount
        if dim == 'left': self.rect.left -= amount
        if dim in ['top','bottom']: self.rect.height += amount
        if dim in ['left','right']: self.rect.width += amount

class Rectangle(Shape):
    """Defines a rectangular interest area
    """
    def contains(self,point):
        """Return True or False depending on whether the point is contained in the interest area
        """
        return self.rect.collidepoint(point)
    
class Ellipse(Shape):
    """Defines an elliptical interest area
    """
    def contains(self,point):
        """Return True or False depending on whether the point is contained in the interest area
        """
        return ((float(point[0]) - self.rect.centerx) / (self.rect.width / 2))**2 + ((float(point[1]) - self.rect.centery)/(self.rect.height / 2))**2 <= 1
