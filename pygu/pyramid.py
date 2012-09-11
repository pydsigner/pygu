'''
Copyright (c) 2011-2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>

 PYREMD (PYgame REsource Management for Developers), or Pyramid, is a resource 
management solution for Pygame. It is designed to be a buffer and interface 
between the game state and your objects that is simpler, easier, and more 
powerful than passing myriads of Pygame groups around (not to mention being 
more Pythonistic). It also attempts to solve the problem of allowing classes to 
do their own image loading while reserving the ability to customize it. 
 
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

__version__ = '1.14.2'

import importlib
import random
import os
import sys
import pygame

from os import listdir as ls
from os.path import join

from pms import Playlist
from common import get_ext

from pgpu.math_utils import limit

# an advanced feature that allows loading a start time for musics
# as well as a certain decision between ogg music and ogg sounds
loaders = {}
# Use the pyslim interface to any available loaders
import pyslim
# The default; presents all the interface we need
dummy = lambda filename: {}
for ext in ['ogg', 'mp3']:
    loaders[ext] = pyslim.ldict.get(ext, dummy)
del dummy

IMAGE_TYPES = ['jpg', 'jpeg', 'jpe', 'png', 'gif', 'bmp', 'pcx', 'pcc', 'tga', 
        'tif', 'tiff', 'lbm', 'pbm', 'pgm', 'ppm', 'xpm']

T_IMAGE = 0
T_SOUND = 1
T_MUSIC = 2
T_CODE = 3
T_PLAYLIST = 4
T_OTHER = 5

METAEVENT = 31

def guess_type(fl):
    ext = get_ext(fl)
    if ext in IMAGE_TYPES:
        return T_IMAGE
    elif ext in ['wav']:
        return T_SOUND
    elif ext in ['mp3']:
        return T_MUSIC
    elif ext in ['ogg']:
        tag = loaders[ext](fl).get('gtype')
        if tag != None:
            # trump the 100 KB rule by setting the gtype tag in metadata
            return int(tag)
        elif os.path.getsize(fl) > 1024 * 100:    # 100 KB
            return T_MUSIC
        else:
            return T_SOUND
    elif ext in ['py', 'pyc']:
        return T_CODE
    elif ext in ['pms']:
        return T_PLAYLIST
    else:
        return T_OTHER


class Sound(pygame.mixer.Sound):
    def __init__(self, snd, resources):
        pygame.mixer.Sound.__init__(self, snd)
        self.resources = resources
        self.set_volume()
    def play(self, *args, **kw):
        self.resources.get_channel().play(self, *args, **kw)
    def set_volume(self):
        pygame.mixer.Sound.set_volume(self, self.resources.s_vol)


class Resources(object):
    '''
    The Resources() object handles the loading and retrieving of objects. 
    
    It is simple to load sounds and images, but advanced music management 
    and code loading are also possible. For sounds and images, the name of 
    the directories is important for retrieving them. The dir in which they 
    are located is known as the 'group'. Once loaded, these objects can be 
    retrieved using its group and title, which is its filename in lowercase 
    without the path or extension. A retrieved image is returned as a ready 
    to use pygame Surface(), and a sound is returned as a special subclass 
    of the pygame Sound() class whose volume is tied to the Resources() 
    instance and can be changed using `.set_s_vol()`. Musics are loaded 
    similarly to sounds or images; however, they are not available for 
    external use, as they cannot be preloaded. Rather, Music playback is 
    handled by playlists. These playlists are in a PMS (Pyramid MetaSong) 
    format, which is described in the `pms` module.
    
    The external interface can be controlled by changing the playlist (the 
    name of which is determined by the file's name) (`.set_playlist()`), the 
    volume (`.set_m_vol()`), and going to the next track (`.next_song()`). 
    Pausing and unpausing playback can be done using 
    `pygame.mixer.music.pause()` and `pygame.mixer.music.unpause()` and is 
    not managed by this object. When a track ends, your program should 
    notify the Resource() object by calling `.track_finished()`.
    
    If you wish to use the code loading features of Resources(), there are 
    some important things to remember. First, the code files must be 
    positioned in the same way as a image or sound. For instance, if you 
    search 'this/dir', your main code files must be in this/dir/*. Also, the 
    main code files must be named '__init__.py' or '__init__.pyc' for import 
    as a package. This method of loading code also requires that the names 
    of folders containing code must follow Python naming requirements. Once 
    your file has been identified, the loader will import and run a function 
    in your file that must be called 'get_objects()', must return a list of 
    objects to be loaded, and accept one argument, which will be the @callwith 
    argument passed to load_objects(). Each of the objects returned must also 
    have a 'title' attribute, which is how it can be retrieved from the 
    Resources() object.The name of the package, though it has no effect upon 
    the names of the objects within, determines order of import. This is 
    essential if your package has dependencies. For example, let us suppose 
    that you are creating a package. If You have a dependency named 
    "super_addon_pack", you cannot name your package "reloading". It must be 
    alphabetically after "super_addon_pack". Supposing the loader is running 
    on '~/.inevitable/data', a possible mainfile would be 
    '~/.inevitable/data/trigger/__init__.py'.
    '''
    def __init__(self, channels=16, dynamic=False):
        '''
        The number of sound channels can be set using @channels, and can be 
        allowed to grow on demand by making @dynamic true.
        '''
        self.reset()
        self.channels = channels
        self.dynamic = bool(dynamic)
        pygame.mixer.set_num_channels(channels)
    
    def reset(self):
        self.music = {}
        self.sounds = {}
        self.images = {}
        self.code = {}
        self.playlists = {}
        self.cur_playlist = ''
        self.m_vol = .13
        self.s_vol = .13
    
    ### Internal loader methods
    
    def load_image(self, loc, title, group):
        '''
        Used internally when loading images. You should probably use 
        load_objects().
        '''
        self.images.setdefault(group, {})
        self.images[group][title] = pygame.image.load(loc).convert_alpha()
    
    def load_music(self, loc, title, group):
        '''
        Used internally when loading music. You should probably use 
        load_objects().
        '''
        self.music.setdefault(group, {})
        self.music[group][title] = loc
    
    def load_playlist(self, loc, title):
        '''
        Used internally when loading playlists. You should probably use 
        load_objects().
        '''
        lines = [l.strip() for l in open(loc).readlines()]
        self.playlists.setdefault(title, [])
        self.playlists[title].append(Playlist(lines, True))
    
    def load_sound(self, loc, title, group):
        '''
        Used internally when loading sounds. You should probably use 
        load_objects().
        '''
        self.sounds.setdefault(group, {})
        self.sounds[group][title] = Sound(loc, self)
    
    def load_code(self, path, package, callwith):
        '''
        Used internally when loading code. You should probably use 
        load_objects().
        '''
        sys.path = [path] + sys.path
        g_o = importlib.import_module(package).get_objects
        del sys.path[0]
        for obj in g_o(callwith):
            self.code[obj.title.lower()] = obj
    
    
    def load_objects(self, dirs=[], callwith={}):
        '''
        Call this to load resources from each dir in @dirs. Code resources will 
        receive @callwith as an argument.
        '''
        for d in dirs:
            contents = ls(d)
            for t in contents:
                first = join(d, t)
                if t.startswith('.') or os.path.isfile(first):
                    continue
                t_l = t.lower()
                for fl in ls(first):
                    full = join(first, fl)
                    if fl.startswith('.') or os.path.isdir(full):
                        continue
                    fl_n = fl.lower().rsplit('.', 1)[0]
                    ty = guess_type(full)
                    if ty == T_IMAGE:
                        self.load_image(full, fl_n, t)
                    elif ty == T_SOUND:
                        self.load_sound(full, fl_n, t)
                    elif ty == T_MUSIC:
                        self.load_music(full, fl_n, t)
                    elif ty == T_CODE and fl_n == '__init__':
                        self.load_code(d, t, callwith)
                    elif ty == T_PLAYLIST:
                        self.load_playlist(full, fl_n)
    
    
    def get_playlist(self):
        return random.choice(self.playlists[self.cur_playlist])
    
    def set_music(self, plylst, force=False):
        '''
        Use to set the playlist to @plylst. If @force is False, the playlist 
        will not be set if it is @plylst already.
        '''
        plylst = plylst.lower()
        if plylst != self.cur_playlist or force:
            self.cur_playlist = plylst
            self.play_song(self.get_playlist().begin())
    
    def next_song(self):
        '''
        Go to the next song in the playlist.
        '''
        self.play_song(self.get_playlist().next())
    
    def play_song(self, stup):
        group, title = stup
        f = self.music[group][title]
        pygame.mixer.music.load(f)
        ext = get_ext(f)
        # Can take a start time from the music's metadata!
        pygame.mixer.music.play(0, float(loaders[ext](f).get('gstart', [0])[0]))
    
    ### Change volumes
    
    def set_m_vol(self, vol=None, relative=False):
        '''
        Set the music volume. If @vol != None, It will be changed to it (or by 
        it, if @relative is True.)
        '''
        if vol != None:
            if relative:
                vol += self.m_vol
            self.m_vol = min(max(vol, 0), 1)
        pygame.mixer.music.set_volume(self.m_vol)
    
    def set_s_vol(self, vol=None, relative=False):
        '''
        Set the volume of all sounds. If @vol != None, It will be changed to 
        it (or by it, if @relative is True.)
        '''
        if vol != None:
            if relative:
                vol += self.s_vol
            self.s_vol = min(max(vol, 0), 1)
        for sgroup in self.sounds.values():
            for snd in sgroup.values():
                snd.set_volume()
    
    ### Resource fetchers
    
    def get_sound(self, title, group):
        '''
        Retrieve sound @title from group @group.
        '''
        return self.sounds[group.lower()][title.lower()]
    def get_image(self, title, group):
        '''
        Retrieve image @title from group @group.
        '''
        return self.images[group.lower()][title.lower()]
    def get_code(self, title):
        '''
        Retrieve code object @title.
        '''
        return self.code[title.lower()]
    
    def get_channel(self):
        '''
        Used internally when playing sounds.
        '''
        c = pygame.mixer.find_channel(not self.dynamic)
        while c is None:
            self.channels += 1
            pygame.mixer.set_num_channels(self.channels)
            c = pygame.mixer.find_channel()
        return c


class GameState(object):
    '''
    This class is designed to be a holder for any sort of data you wish to 
    pass around, such as the Resources() class in this module.
    '''
    
    def __init__(self, groups={}):
        self.groups = {}
    
    ### Group control methods
    
    def add_groups(self, groups={}):
        self.groups.update(groups)
    
    def remove_group(self, group):
        del self.groups[group]
    
    def remove_groups(self, groups=[]):
        for group in groups:
            self.remove_group(group)
    
    def get_group(self, group):
        return self.groups[group]
    
    def get_groups(self, groups=[]):
        res = {}
        for group in groups:
            res[group] = self.get_group(group)
        return res
    
    def empty_groups(self):
        self.groups.clear()


class EventManager(object):
    '''
    An event manager for complex applications with a necessity for run-time 
    customizable event handling.
    '''
    class Message(Exception):
        pass
    
    class MetaEvent(object):
        def __init__(self, event):
            self.__dict__['e'] = event
        def __getattr__(self, attr):
            if attr == 'type':
                attr = 'utype'
            return getattr(self.__dict__['e'], attr)
        def __setattr__(self, attr, value):
            if attr == 'type':
                attr = 'utype'
            setattr(self.__dict__['e'], attr, value)
    
    def __init__(self, gstate):
        '''
        @gstate should be whatever you want sent to the registered functions.
        '''
        self.gstate = gstate
        self.event_funcs = {}
    
    ### Event registering
    
    def bind(self, func, etype):
        '''
        Register @func for execution when events with `.type` of @etype 
        or meta-events with `.utype` of @etype are handled. @func will be 
        called with self, self.gstate, and the event as arguments.
        '''
        self.event_funcs.setdefault(etype, [])
        # Don't add multiple times!
        if func not in self.event_funcs[etype]:
            self.event_funcs[etype].append(func)
    
    def unbind(self, func, etype):
        '''
        Remove @func from the execution list for events with `.type` of @etype 
        or meta-events with `.utype` of @etype. If @func is not in said list, 
        a ValueError will be raised.
        '''
        i= self.event_funcs[etype].index(func)
        del self.event_funcs[etype][i]
    
    ### pygw.Container() compatibility methods
    
    def convert_point(self, point):
        '''
        Converts the relative position of @point into an absolute position. 
        Does nothing in this class, but exists for the sake of the 
        pygw.Container() class.
        '''
        return point
    
    def convert_rect(self, rect):
        '''
        Converts the relative position of @rect into an absolute position. Does 
        nothing in this class, but exists for the sake of the pygw.Container() 
        class.
        '''
        return rect
    
    ### Meta-event utility method
    
    def event(self, utype, **kw):
        '''
        Make a meta-event with a utype of @type. **@kw works the same as for 
        pygame.event.Event().
        '''
        d = {'utype': utype}
        d.update(kw)
        pygame.event.post(pygame.event.Event(METAEVENT, d))
    
    ### Event loop
    
    def loop(self, events=[]):
        '''
        Run the loop.
        '''
        try:
            for e in events:
                if e.type == METAEVENT:
                    e = self.MetaEvent(e)
                for func in self.event_funcs.get(e.type, []):
                    func(self, self.gstate, e)
        except self.Message as e:
            return e.message


class HotspotManager(object):
    '''
    An addon to EventManager that allows dynamic mouse-action-in-area binding.
    '''
    def __init__(self, emanager):
        self.dynamic = []
        self.static = []
        emanager.bind(self.execute, pygame.MOUSEBUTTONDOWN)
        emanager.bind(self.execute, pygame.MOUSEBUTTONUP)
        emanager.bind(self.exec_hover, pygame.MOUSEMOTION)
        self.emanager = emanager
    
    def __del__(self):
        self.emanager.unbind(self.execute, pygame.MOUSEBUTTONDOWN)
        self.emanager.unbind(self.execute, pygame.MOUSEBUTTONUP)
        self.emanager.unbind(self.exec_hover, pygame.MOUSEMOTION)
    
    ### Event registration
    
    def add_static(self, cfuncs, rect, absolute=True):
        '''
        @cfuncs is a (button_action_func, hover_func) tuple. button_action_func 
        should have a 
        func(EventManager, GameState, Event) 
        signature, whereas hover_func should have a 
        func(EventManager, GameState, Event, bool: "Is mouse hovering?") 
        signature.
        
        Adds @cfuncs statically; that is, it will be called whenever the 
        mouse is clicked inside @rect.
        '''
        self.static.append((cfuncs, rect))
    
    def add_dynamic(self, cfuncs, rfunc):
        '''
        @cfuncs is a (button_action_func, hover_func) tuple. button_action_func 
        should have a 
        func(EventManager, GameState, Event) 
        signature, whereas hover_func should have a 
        func(EventManager, GameState, Event, bool: "Is mouse hovering?") 
        signature.
        
        Adds @cfuncs dynamically; that is, it will be called whenever the 
        mouse is clicked inside any of the Rect()s provided by @rfunc.
        '''
        self.dynamic.append((cfuncs, rfunc))
    
    ### Event handling
    
    def execute(self, eman, gstate, event):
        loc = event.pos
        for t in self.static:
            if t[0][0] is None:
                continue
            if t[1].collidepoint(loc):
                t[0][0](eman, gstate, event)
        for t in self.dynamic:
            if t[0][0] is None:
                continue
            for r in t[1](gstate):
                if r.collidepoint(loc):
                    t[0][0](eman, gstate, event)
                    break
    
    def exec_hover(self, eman, gstate, event):
        loc = event.pos
        for t in self.static:
            if t[0][1] is None:
                continue
            t[0][1](eman, gstate, event, t[1].collidepoint(loc))
        for t in self.dynamic:
            if t[0][1] is None:
                continue
            for r in t[1](gstate):
                y = False
                if r.collidepoint(loc):
                    y = True
                    break
            t[0][1](eman, gstate, event, y)


class EventManagerPlus(EventManager):
    '''
    A version of EventManager with a builtin HotspotManager.
    '''
    def __init__(self, gstate):
        EventManager.__init__(self, gstate)
        self.hotspot = HotspotManager(self)


class StateManager(GameState):
    '''
    A GameState with a state model. Each state has an EventManagerPlus for 
    separation of events.
    '''
    def __init__(self, states, groups={}):
        self.states = {}
        self.add_states(*states)
        self.state = states[0]
        GameState.__init__(self, groups)
    
    def __getitem__(self, key):
        return self.states[key]
    
    ### State manipulation methods
    
    def add_states(self, *states):
        '''
        Add @states.
        '''
        for state in states:
            self.states[state] = EventManagerPlus(self)
    
    def get_state(self, state=None):
        '''
        If @state is None, return the title of the current state. Otherwise, 
        return the EventManager for @state.
        '''
        return self._state if state is None else self.states[state]
    
    def get_states(self):
        return self.states
    
    def set_state(self, state):
        '''
        Set the state to @state.
        '''
        self._state = state
    state = property(get_state, set_state)
    
    ### Event loop
    
    def loop(self, events=[]):
        '''
        Run the event processing loop with @events.
        '''
        # MUST return loop (see what the loop may return.)
        return self[self.state].loop(events)

