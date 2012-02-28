'''
Copyright (c) 2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>

PyGW (PYdsigner's PYGame Gui Widgets) is a Pygame GUI toolkit designed to mesh 
with Pyramid's event management system. It imposes minimal restraints on the 
developer, who is then free to customise his widget to the extent he desires.

--------------------------------------------------------------------------------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = '1.3'

import string
from pgpu.math_utils import Vector, limit

from common import vcenter_blit

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
        if is_hovered and not self.hover:
            self.hover = True
            self.image = self.content[1]
        elif not is_hovered and self.hover:
            self.hover = False
            self.image = self.content[0]

class Typable(Label):
    '''
    A base class for widgets that can typed in.
    
    NOTE: Be sure to call update() every frame, or changes won't show up.
    '''
    def __init__(self, groups, pos, warea, content, eman, **kw):
        '''
        Required Args:
        See documentation for Label();
        @warea, the area in which to check for clicks inside or outside the 
         widget.
        
        Optional Keyword Args:
        @font, the pygame font to be used for drawing the text (Defaults to the 
         default pygame font in size 18);
        @color, the color to be used for drawing the text (Defaults to black);
        @margin, the text offset from the left side of the widget (Defaults to 
         no margin).
        '''
        Label.__init__(self, groups, pos, content, eman)
        
        self.blank = content
        self.font = kw.pop('font', pygame.font.Font(None, 18))
        self.color = kw.pop('color', (0, 0, 0))
        self.margin = (kw.pop('margin', 0), 0)
        if kw:
            raise TypeError(
                    'These keyword args are not allowed: %s' % kw.keys())
        
        self.focus = False
        self.reset()
        
        eman.hotspot.add_static([self.click_cb, lambda *args: None], warea)
        eman.bind(self.type_cb, KEYDOWN)
    
    def reset(self):
        self.text = []
        self.cursor_loc = 0
    
    def click_cb(self, eman, gstate, event):
        self.focus = True if self.rect.collidepoint(event.pos) else False
    
    def type_cb(self, eman, gstate, event):
        if not self.focus:
            return
        if (event.unicode and event.unicode in string.printable 
                and event.key != K_RETURN):
            self.insert(event.unicode)
        elif event.key == K_BACKSPACE:
            self.bspace()
        else:
            self.handle_other(event)
    
    def handle_other(self, event):
        '''
        Override this to implement such things as delete and navigation.
        '''
    
    def get(self):
        '''
        Get the text from the Typable().
        '''
        return ''.join(self.text)
    
    def insert(self, s):
        '''
        Insert string @s at the current cursor location.
        '''
        for c in s:
            self.text.insert(self.cursor_loc, c)
            self.cursor_loc += 1
    
    def bspace(self):
        '''
        Remove the character before the cursor.
        '''
        try:
            self.text.pop(self.cursor_loc - 1)
            self.cursor_loc -= 1
        except IndexError:
            pass
    
    def update(self):
        '''
        Update the image before drawing.
        '''
        self.image = self.blank.copy()
        vcenter_blit(self.image, 
                self.font.render(self.get(), True, self.color), 
                self.margin)

class Entry(Typable):
    '''
    A full featured Entry widget, which supports navigation, a cursor, delete,
    and rudimentary copy-cut-paste (All of the widget's contents are 
    copied/cut).
    '''
    def __init__(self, groups, pos, warea, content, cursor, eman, **kw):
        '''
        Required Args:
        See documentation for Typable();
        @cursor, the pygame surface that will be used as the cursor.
        
        Optional Keyword Args:
        See documentation for Typable;
        @callback, the function to call when Enter is hit, will be called with 
         the Widget() as the only argument (Defaults to a null function);
        @blink_frames, the number of updates before flipping the cursor from 
         shown to hidden or vice versa (Defaults to None, never hide the 
         cursor.)
        '''
        self.enter_cb = kw.pop('callback', lambda widget: None)
        self.blink_frames = kw.pop('blink_frames', None)
        
        Typable.__init__(self, groups, pos, warea, content, eman, **kw)
        
        self.blinker = 1
        self.cursor_shown = True
        
        self.cursor = cursor
        pygame.scrap.init()
    
    def delete(self):
        '''
        Remove the character after the cursor.
        '''
        try:
            self.text.pop(self.cursor_loc)
        except IndexError:
            pass
    
    def copy(self):
        '''
        Copy the text in the Entry() and place it on the clipboard.
        '''
        try:
            pygame.scrap.put(SCRAP_TEXT, self.get())
        except:
            # pygame.scrap is experimental, allow for changes
            pass
    
    def cut(self):
        '''
        Cut the text in the Entry() and place it on the clipboard.
        '''
        self.copy()
        self.reset()
    
    def paste(self):
        '''
        Insert text from the clipboard at the cursor.
        '''
        try:
            t = pygame.scrap.get(SCRAP_TEXT)
            if t:
                self.insert(t)
        except:
            # pygame.scrap is experimental, allow for changes
            pass
    
    def handle_other(self, event):
        if event.mod & KMOD_CTRL:
            if event.key == K_c:
                self.copy()
            elif event.key == K_x:
                self.cut()
            elif event.key == K_v:
                self.paste()
        
        elif event.key == K_HOME:
            self.cursor_loc = 0
        elif event.key == K_END:
            self.cursor_loc = len(self.text)
        elif event.key == K_DELETE:
            self.delete()
        elif event.key == K_RETURN:
            self.enter_cb(self)
        elif event.key == K_RIGHT:
            self.cursor_loc += 1
        elif event.key == K_LEFT:
            self.cursor_loc -= 1
        self.cursor_loc = limit(self.cursor_loc, 0, len(self.text))
    
    def update(self):
        '''
        Update the image before drawing.
        '''
        self.image = self.blank.copy()
        
        bf = self.font.render(''.join(self.text[:self.cursor_loc]), 
                True, self.color)
        br = bf.get_rect().move(self.margin)
        
        af = self.font.render(''.join(self.text[self.cursor_loc:]), 
                True, self.color)
        
        cr = self.cursor.get_rect()
        cvec = Vector(br.w - cr.w, 0) + self.margin
        
        vcenter_blit(self.image, bf, br)
        vcenter_blit(self.image, af, br.topright)
        
        if self.cursor_shown and self.focus:
            vcenter_blit(self.image, self.cursor, cvec)
        
        if self.blink_frames != None:
            self.blinker += 1
            self.blinker %= self.blink_frames
            if not self.blinker:
                self.cursor_shown = not self.cursor_shown


class ScrollBar(ClickableWidget):
    '''
    A ScrollBar Widget().
    
    * Supports mouse-wheels.
    TODO: Implement!
    '''

class Scrollable(Label):
    '''
    A wrapper Widget() to allow scrolling. Supports ScrollBar()s.
    '''
    def __init__(self, widget, groups, bg, pos, eman):
        Label.__init__(self, groups, pos, bg, eman)
        self.widget = widget
        self.image = widget.image.copy()
        self.wrect = widget.rect.copy()
        widget.rect = self.rect
        
        self.bg = bg
        self.offset = Vector()
    
    def scroll_x(self, pixels, relative=True):
        '''
        Negative is right, positive is left.
        '''
        if relative:
            self.offset.x += int(pixels)
        else:
            self.offset.x = int(pixels)
        
    def scroll_y(self, pixels, relative=True):
        '''
        Negative is down, positive is up.
        '''
        if relative:
            self.offset.y += int(pixels)
        else:
            self.offset.y = int(pixels)
    
    def update(self):
        self.image = self.bg.copy()
        
        self.offset.x = limit(self.offset.x, 
                -self.wrect.w + self.rect.w, 0)
        self.offset.y = limit(self.offset.y, 
                -self.wrect.h + self.rect.h, 0)
        
        self.image.blit(self.widget.image, self.offset)
