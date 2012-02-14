'''
Copyright (c) 2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>

PyGW (PYdsigner's PYGame Gui Widgets) is a Pygame GUI toolkit designed to mesh 
with Pyramid's event management system. It imposes minimal restraints on the 
developer, who is then free to customise his widget to the extent he desires.

--------------------------------------------------------------------------------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = '1.1'

import pygame
from pygame.locals import *
pygame.init()

class Widget(pygame.sprite.Sprite):
    '''
    Widget() provides the base for all other Widget()s. See Label() for a 
    reference Widget().
    '''

class Label(Widget):
    '''
    A basic Widget() that simply displays some content.
    '''
    def __init__(self, groups, pos, content, eman):
        '''
        @groups is a list of the groups to which the Label() should be added;
        @pos is the position of the upper-left corner of the Label();
        @content is the Surface() to display;
        @gstate is a reference (unused by this simple class) to an 
         EventManagerPlus() object.
        '''
        Widget.__init__(self, *groups)
        self.rect = content.get_rect()
        self.rect.move_ip(pos)
        self.image = content
        self.eman = eman

class ClickableWidget(Label):
    '''
    A base class for clickable Widget()s.
    '''
    def __init__(self, groups, pos, content, eman):
        '''
        See documentation for Label();
        @eman *is* used, so don't supply a dummy!
        '''
        Label.__init__(self, groups, pos, content, eman)
        eman.hotspot.add_dynamic((self.callback, self.set_hover), self.get_rect)
    
    def callback(self, eman, gstate, event):
        pass
    
    def set_hover(self, eman, gstate, event, is_hovered):
        pass
    
    def get_rect(self, gstate):
        return [self.rect]

class Button(ClickableWidget):
    '''
    A basic Button Widget().
    '''
    def __init__(self, groups, pos, content, callback, eman):
        '''
        See documentation for ClickableWidget();
        @content should be a (normal_content, active_content) tuple;
        @callback: The function to be called when the Button() is clicked.
        '''
        self.cb = callback
        self.hover = False
        self.content = content
        ClickableWidget.__init__(self, groups, pos, content[0], eman)
    
    def callback(self, eman, gstate, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.cb(eman, gstate, event)
    
    def set_hover(self, eman, gstate, event, is_hovered):
        # Save time by not assigning unneccessarily.
        if is_hovered and not self.hover:
            self.hover = True
            self.image = self.content[1]
        elif not is_hovered and self.hover:
            self.hover = False
            self.image = self.content[0]

class ScrollBar(ClickableWidget):
    '''
    A ScrollBar Widget().
    
    * Supports mouse-wheels.
    TODO: Implement!
    '''

class Scrollable(Widget):
    '''
    A wrapper Widget() to allow scrolling. Supports ScrollBar()s.
    TODO: Implement!
    '''
