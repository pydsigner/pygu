'''
Shared information, classes and functions for PyGU.
'''
from pgpu.math_utils import Vector

def get_ext(fl):
    return fl.split('.')[-1].lower()

def vcenter_blit(target, source, dest = (0, 0), area=None, special_flags=0):
    '''
    Blits surface @source in a vertically centered manner to surface @target. 
    Takes the normal Surface.blit() flags; however, @dest is used as an offset.
    '''
    toblit = source.subsurface(area) if area != None else source
    
    loc = (Vector(0, target.get_height() / 2) + dest - 
            Vector(0, toblit.get_height() / 2))
    
    target.blit(toblit, loc, special_flags = special_flags)
