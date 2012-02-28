'''
Shared information, classes and functions for PyGU.
'''
from pgpu.math_utils import Vector

def get_ext(fl):
    return fl.split('.')[-1].lower()


def _blitter(loc, target, source, dest, area, special_flags):
    toblit = source.subsurface(area) if area != None else source
    target.blit(toblit, loc + dest, special_flags = special_flags)

def center_blit(target, source, dest = (0, 0), area=None, special_flags=0):
    '''
    Blits surface @source to the center of surface @target. Takes the normal 
    Surface.blit() flags; however, @dest is used as an offset.
    '''
    loc = Vector(target.get_size()) / 2 - Vector(toblit.get_size()) / 2
    _blitter(loc, target, source, dest, area, special_flags)

def vcenter_blit(target, source, dest = (0, 0), area=None, special_flags=0):
    '''
    The same as center_blit(), but only centers vertically.
    '''
    loc = (Vector(0, target.get_height() / 2) - 
            Vector(0, toblit.get_height() / 2))
    _blitter(loc, target, source, dest, area, special_flags)

def hcenter_blit(target, source, dest = (0, 0), area=None, special_flags=0):
    '''
    The same as center_blit(), but only centers horizontally.
    '''
    loc = (Vector(target.get_width() / 2, 0) - 
            Vector(toblit.get_width() / 2, 0))
    _blitter(loc, target, source, dest, area, special_flags)
