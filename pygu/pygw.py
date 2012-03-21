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
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = '2.0'

import string
import itertools
from pgpu.math_utils import Vector, limit

from common import vcenter_blit

import pygame
from pygame.locals import *


def is_container(c):
    '''
    Utility function to check for containerhood.
    '''
    return getattr(c, '_iscontainer', False) or isinstance(c, Container)


def is_widget(w):
    '''
    Utility function to check for widgetness.
    '''
    return getattr(w, '_iswidget', False) or isinstance(w, Widget)


class Base(object):
    '''
    Implements the core for both containers and widgets.
    '''
    _iswidget = _iscontainer = False
    
    def __init__(self, container):
        self.container = None
        
        if is_container(container):
            # Can't add to EventManager()s!
            self.add_to(container)
        else:
            self.add_internal(container)
    
    def __del__(self):
        self.kill()
    
    def update(self):
        '''
        Dummy update method.
        '''
        pass
    
    def kill(self):
        if is_container(self.container):
            self.container.remove(self)
    
    ### Content management
    
    def add_to(self, container):
        '''
        Add the class to @container.
        '''
        if self.container:
            self.remove_from(self.container)
        container.add(self)
    
    def remove_from(self, container):
        '''
        Remove the class from @container.
        '''
        if self in container:
            container.remove(self)
    
    def add_internal(self, c):
        '''
        Used internally to notify the class that @c now contains it.
        '''
        self.container = c
    
    def remove_internal(self, c):
        '''
        Used internally to notify the class that @c no longer contains it.
        '''
        self.container = None


class Container(Base):
    '''
    A combination of a Pygame Group and an EventManager, the Container() is a 
    way to add encapsulation to PyGW. It does much the same job as the Tkinter 
    Frame() widget does.
    
    In practice, the Container() allows its widgets to be oblivious of their 
    position within the pygame display. Instead, they know their position 
    within the Container(), which does all the hard work of translating these 
    relative values into absolute values. This opens up the ability to code 
    mega-widgets, as is possible in any full-desktop GUI toolkit.
    '''
    
    class _WrapCB(object):
        def __init__(self, container, cb):
            self.container = container
            self.cb = cb
        
        def __call__(self, *args, **kw):
            if self.container.shown:
                self.cb(*args, **kw)
    
    _iscontainer = True
    
    def __init__(self, container, pos, shown=True):
        Base.__init__(self, container)
        
        self.containers = set()
        self.widgets = set()
        self._event_cbs = {}
        
        self.shown = shown
        self.pos = Vector(pos)
        
        self.hotspot = container.hotspot
        self.Message = container.Message
    
    def __contains__(self, w):
        return w in self.widgets or w in self.containers
    
    def __iter__(self):
        return itertools.chain(self.widgets, *self.containers)
    
    def update(self):
        for w in self:
            w.update()
    
    def draw(self, surf):
        '''
        Draw all widgets and sub-containers to @surf.
        '''
        if self.shown:
            for w in self.widgets:
                surf.blit(w.image, self.convert_rect(w.rect))
            for c in self.containers:
                c.draw(surf)
    
    def kill(self):
        '''
        Remove the class from its container, contained items and sub-widgets. 
        Runs automatically when the class is garbage collected.
        '''
        Base.kill(self)
        
        for c in self.containers:
            c.remove_internal(self)
        for w in self.widgets:
            w.remove_internal(self)
    
    ### Content control
    
    def add(self, *widgets):
        '''
        Place @widgets under the blitting hand of the Container(). Each arg 
        must be a Widget(), a fellow Container(), or an iterable. Else, things 
        get ugly...
        '''
        for w in widgets:
            if is_widget(w):
                if w not in self.widgets:
                    self.widgets.add(w)
                    w.add_internal(self)
            elif is_container(w):
                if w not in self.containers:
                    self.containers.add(w)
                    w.add_internal(self)
            else:
                # If it isn't an iterable, we'll get an error here.
                # Desired effect.
                self.add(*w)
    
    def remove(self, *widgets):
        '''
        Remove @widgets from the blitting hand of the Container(). Each arg 
        must be a Widget(), a fellow Container(), or an iterable. Else, things 
        get ugly...
        '''
        for w in widgets:
            if w in self.widgets:
                self.widgets.remove(w)
                w.remove_internal(self)
            elif w in self.containers:
                self.containers.remove(w)
                w.remove_internal(self)
            else:
                # If it isn't an iterable, we'll get an error here.
                # Desired effect.
                self.remove(*w)
    
    ### Sub-widget tools
    
    def convert_point(self, point):
        '''
        Converts the relative position of @point into an absolute position. To 
        be used for event considerations, blitting is handled directly by the 
        Container().
        '''
        return self.container.convert_point(Vector(point) + self.pos)
    
    def convert_rect(self, rect):
        '''
        Converts the relative position of @rect into an absolute position.To be 
        used for event considerations, blitting is handled directly by the 
        Container().
        '''
        return self.container.convert_rect(rect.move(self.pos))
    
    ### EventManager() compatibility methods
    
    def event(self, utype, **kw):
        '''
        Delegates to the event manager/container.
        '''
        self.container.event(utype, **kw)
    
    def bind(self, func, etype):
        '''
        Wraps around container.bind().
        '''
        if func not in self._event_cbs:
            wrapped = self._WrapCB(self, func)
            self._event_cbs[func] = wrapped
        else:
            wrapped = self._event_cbs[func]
        self.container.bind(wrapped, etype)
    
    def unbind(self, func, etype):
        '''
        Wraps around container.unbind().
        '''
        wrapped = self.event_cbs[func]
        self.container.unbind(self, wrapped, etype)


class Scrollable(Container):
    '''
    A Container() with scrolling. Can be used with Scrollbar()s.
    
    NOTE: To add a background, add a Label() or other widget of the same size 
    as this widget in the same location. The other widget will be drawn 
    underneath this widget.
    '''
    def __init__(self, eman, pos, size, shown=True):
        Container.__init__(self, eman, pos, shown)
        self.offset = Vector()
        self.size = Vector(size)
    
    def draw(self, surf):
        loc = self.container.convert_point(self.pos)
        msurf = pygame.Surface(loc + self.size, SRCALPHA)
        Container.draw(self, msurf)
        surf.blit(msurf, loc, (loc, loc + self.size))
    
    ### Internal methods
    
    def _get_area(self):
        rs = [w.container.convert_rect(w.rect) for w in self]
        return Rect(0,0,0,0).unionall(rs).size - self.pos
    
    def _update(self):
        x, y = self._get_area()
        self.offset.x = limit(self.offset.x, 0, x - self.size.x)
        self.offset.y = limit(self.offset.y, 0, y - self.size.y)
    
    ### External interface
    
    def scroll_x(self, pixels, relative=True):
        '''
        Negative values for @pixels scroll left, positive values scroll right;
        @relative determines whether to set the scroll-x value or change as 
        above.
        '''
        if relative:
            self.offset.x += int(pixels)
        else:
            self.offset.x = int(pixels)
        self._update()
        
    def scroll_y(self, pixels, relative=True):
        '''
        Negative values for @pixels scroll up, positive values scroll down;
        @relative determines whether to set the scroll-y value or change as 
        above.
        '''
        if relative:
            self.offset.y += int(pixels)
        else:
            self.offset.y = int(pixels)
        self._update()
    
    ### Sub-widget tools
    
    def convert_point(self, point):
        '''
        Same as Container().convert_point(), but adds scrolling.
        '''
        return Container.convert_point(self, point) - self.offset
    
    def convert_rect(self, rect):
        '''
        Same as Container().convert_rect(), but adds scrolling.
        '''
        return Container.convert_rect(self, rect).move(-self.offset)


class Widget(Base):
    '''
    Widget() provides the base for all other Widget()s. See Label() for a 
    reference Widget().
    '''
    _iswidget = True


class Label(Widget):
    '''
    A basic Widget() that simply displays some content.
    '''
    def __init__(self, container, pos, content):
        '''
        @container the container to which the Label() should be added;
        @pos is the position of the upper-left corner of the Label();
        @content is the Surface() to display;
        '''
        Widget.__init__(self, container)
        self.rect = content.get_rect()
        self.rect.move_ip(pos)
        self.image = content


class ClickableWidget(Label):
    '''
    A base class for clickable Widget()s.
    '''
    def __init__(self, container, pos, content):
        '''
        See documentation for Label();
        '''
        Label.__init__(self, container, pos, content)
        container.hotspot.add_dynamic(
                (self.callback, self.set_hover), self.get_rect)
    
    ### Override these
    
    def callback(self, eman, gstate, event):
        pass
    
    def set_hover(self, eman, gstate, event, is_hovered):
        pass
    
    ### Useful defaults
    
    def get_rect(self, gstate):
        return [self.container.convert_rect(self.rect)]


class Button(ClickableWidget):
    '''
    A basic Button Widget().
    '''
    def __init__(self, container, pos, content, callback):
        '''
        See documentation for ClickableWidget();
        @content should be a (normal_content, active_content) tuple;
        @callback: The function to be called when the Button() is clicked.
        '''
        self.cb = callback
        self.hover = False
        self.content = content
        ClickableWidget.__init__(self, container, pos, content[0])
    
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
    def __init__(self, container, pos, warea, content, **kw):
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
        Label.__init__(self, container, pos, content)
        
        self.blank = content
        self.font = kw.pop('font', pygame.font.Font(None, 18))
        self.color = kw.pop('color', (0, 0, 0))
        self.margin = (kw.pop('margin', 0), 0)
        if kw:
            raise TypeError(
                    'These keyword args are not allowed: %s' % kw.keys())
        
        self.focus = False
        self.reset()
        
        container.hotspot.add_static(
                [self.click_cb, lambda *args: None], warea)
        container.bind(self.type_cb, KEYDOWN)
    
    def bspace(self):
        '''
        Remove the character before the cursor.
        '''
        try:
            self.text.pop(self.cursor_loc - 1)
            self.cursor_loc -= 1
        except IndexError:
            pass
    
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
    
    ### External interface
    
    def reset(self):
        '''
        Clear the widget.
        '''
        self.text = []
        self.cursor_loc = 0
    
    def get(self):
        '''
        Get the text from the widget.
        '''
        return ''.join(self.text)
    
    def insert(self, s):
        '''
        Insert string @s at the current cursor location.
        '''
        for c in s:
            self.text.insert(self.cursor_loc, c)
            self.cursor_loc += 1
    
    ### Updater
    
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
    A full featured entry widget, which supports navigation, a cursor, delete,
    autoscroll, and rudimentary copy-cut-paste (All of the widget's contents 
    are copied/cut).
    '''
    def __init__(self, container, pos, warea, content, cursor, **kw):
        '''
        Required Args:
        See documentation for Typable();
        @cursor, the pygame surface that will be used as the cursor.
        
        Optional Keyword Args:
        See documentation for Typable();
        @callback, the function to call when Enter is hit, will be called with 
         the Widget() as the only argument (Defaults to a null function);
        @blink_frames, the number of updates before flipping the cursor from 
         shown to hidden or vice versa (Defaults to None, never hide the 
         cursor.)
        '''
        self.enter_cb = kw.pop('callback', lambda widget: None)
        self.blink_frames = kw.pop('blink_frames', None)
        
        Typable.__init__(self, container, pos, warea, content, **kw)
        
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
            return True
        except:
            # pygame.scrap is experimental, allow for changes
            return False
    
    def cut(self):
        '''
        Cut the text in the Entry() and place it on the clipboard.
        '''
        if self.copy():
            self.reset()
    
    def paste(self):
        '''
        Insert text from the clipboard at the cursor.
        '''
        try:
            t = pygame.scrap.get(SCRAP_TEXT)
            if t:
                self.insert(t)
                return True
        except:
            # pygame.scrap is experimental, allow for changes
            return False
    
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
        
        scroll = Vector()
        
        if cvec.x > self.rect.w:
            scroll.x = self.rect.w - cvec.x - self.font.size(' ')[0]
        
        vcenter_blit(self.image, bf, scroll + br)
        vcenter_blit(self.image, af, scroll + br.topright)
        
        if self.cursor_shown and self.focus and pygame.key.get_focused():
            vcenter_blit(self.image, self.cursor, scroll + cvec)
        
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
