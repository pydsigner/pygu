'''
Copyright (c) 2011-2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>

 This module is a loader for PMS (Pyramid MetaSong) playlists, which are 
 described in the doc for Playlist().

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

import random

__version__ = '1.2.2'

class Playlist(object):
    '''
    Pyramid MetaSong Playlist
    
    A PMS playlist looks somewhat like this:
    
    /home/pydsigner/Music;/home/pydsigner/programming/musics
    group1/music2.group5/music8
    group4/music1.group4/music2
    group7/music5
    *2*group8/music2^group8/music3.group8/music4
    
    The first line can be left blank, and is intended stand-alone playlists;
    It gives PMS players a list of folders in which to search for the group 
    folders. After the first line, every line of the playlist is a metasong 
    that may span several files. If, as in the example above, the second line 
    (group1/music2.group5/music8) is not blank, it will be played first but 
    only once. After one metasong is complete, another is selected. The musics 
    of a metasong are identified by a '<group>/<title>' combo as on line 2. If 
    multiple musics are desired, they must be separated by a '.' as on line 2. 
    If, as on the last line, there is a '^' separator, then the musics before 
    the '^' will be played only when the metasong is newly selected; that is, 
    when the metasong that just finished is not the newly selected metasong. 
    This means that 'group8/music2' could be an intro for an unlimited loop of 
    'group8/music3' and 'group8/music4'.Also note the *2*: this tells the 
    playlist to give a double chance of selecting to this metasong when shuffle 
    is on. This value must be a positive integer, be at the beginning of a 
    metasong, and be between two asterisks.
    
    This implementation supports v1.2 weighted shuffling and folder hints.
    '''
    
    perrm = 'The parser encountered an error while parsing line %s!'
    
    def __init__(self, lines, shuffle=False, strict=True):
        '''
        @lines is a list of the PMS lines to load. @shuffle, which may be 
        changed later using the `.shuffle` attribute, determines whether to 
        shuffle the metasongs. @strict determines whether erroneous lines 
        should raise an error or simply be ignored.
        '''
        self.folders = lines[0].split(';') if lines else []
        try:
            self.start = ([m.split('/') for m in lines[1].split('.')] if 
                    lines[1] else [])
        except:
            if strict:
                raise ValueError(self.perrm % 1)
            self.start = []
        
        self.loop = []
        lcount = 1
        
        for line in lines[2:]:
            lcount += 1
            try:
                if not line:
                    continue
                ul = line
                
                # Shuffle weight: new to version 1.2
                chance = 1      # default shuffle weight is 1
                # if there is a specified shuffle weight, use it!
                if ul.startswith('*'):
                    e = ul[1:].find('*') + 1
                    chance = int(ul[1:e])
                    # We don't want to try to parse the weight!
                    ul = ul[e + 1:]
                song = [[m.split('/') for m in group.split('.')] 
                        for group in ul.split('^', 2)]
            except:
                if strict:
                    raise ValueError(self.perrm % lcount)
                continue
            self.loop.append((song, chance))
        
        self.shuffle = shuffle
        self.pos = 0
        self.at_beginning = False
        self.song = 0
        
        self._gen_shuffles()
    
    def _gen_shuffles(self):
        '''
        Used internally to build a list for mapping between a random number and 
        a song index.
        '''
        # The current metasong index 
        si = 0
        # The shuffle mapper list
        self.shuffles = []
        # Go through all our songs...
        for song in self.loop:
            # And add them to the list as many times as they say to.
            for i in range(song[1]):
                self.shuffles.append(si)
            si += 1
    
    def _new_song(self):
        '''
        Used internally to get a metasong index.
        '''
        # We'll need this later
        s = self.song
        
        if self.shuffle:
            # If shuffle is on, we need to (1) get a random song that 
            # (2) accounts for weighting. This line does both.
            self.song = self.shuffles[random.randrange(len(self.shuffles))]
        else:
            # Nice and easy, just get the next song...
            self.song += 1
            # But wait! need to make sure it exists!
            if self.song >= len(self.loop):
                # It doesn't, so start over at the beginning.
                self.song = 0
        # Set flag if we have the same song as we had before.
        self.dif_song = s != self.song
        # Reset the position within the metasong
        self.pos = 0
    
    def _get_selectable(self):
        '''
        Used internally to get a group of choosable tracks.
        '''
        # Save some typing
        cursong = self.loop[self.song][0]
        
        if self.dif_song and len(cursong) > 1:
            # Position is relative to the intro of the track,
            # so we we will get the both the intro and body.
            s = cursong[0] + cursong[1]
        else:
            # Position is relative to the body of the track, so just get that.
            s = cursong[-1]
        # Return what we found
        return s
    
    def _get_song(self):
        '''
        Used internally to get the current track and make sure it exists.
        '''
        # Try to get the current track from the start metasong
        if self.at_beginning:
            # Make sure it exists.
            if self.pos < len(self.start):
                # It exists, so return it.
                return self.start[self.pos]
            # It doesn't exist, so let's move on!
            self.at_beginning = False
            # Generate a new track selection
            self._new_track()
        # A bit more difficult than using the start metasong, 
        # because we could have a beginning part. Call a function that gets all 
        # applicable tracks from the metasong.
        s = self._get_selectable()
        # Make sure it is long enough
        while self.pos >= len(s):
            # Or pick a new metasong.
            self._new_song()
            # And repeat.
            s = self._get_selectable()
        # Found a track, return it.
        return s[self.pos]
    
    def begin(self):
        '''
        Start over and get a track.
        '''
        # Check for a start metasong
        if self.start:
            # We are in the beginning song
            self.at_beginning = True
            # And on the first track.
            self.pos = 0
        else:
            # We aren't in the beginning song
            self.at_beginning = False
            # So we need to get new one.
            self._new_song()
        return self._get_song()
    
    def next(self):
        '''
        Get the next track.
        '''
        self.pos += 1
        return self._get_song()
    
    def next_song(self):
        '''
        Skip to the next song and return a track.
        '''
        self._new_song()
        return self._get_song()
