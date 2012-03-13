'''
Copyright (c) 2011-2012 Daniel Foerster/Dsigner Software <pydsigner@gmail.com>

PySLMM (Python Seamless Music Metadata), or PySlim, is intended to be a music 
metadata loader that can seamlessly load metadata using any of the various 
metadata loaders available. In other words, PySlim is a script's frontend to 
music metadata loaders.

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

__version__ = '1.0.2'
__all__ = ['load']

import importlib

loaders = []
ldict = {}


def load(filename, default=None):
    '''
    Try to load @filename. If there is no loader for @filename's filetype, 
    return @default.
    '''
    ext = get_ext(filename)
    if ext in ldict:
        return ldict[ext](filename)
    else:
        return default


def _loader(d):
    res = {}
    try:
        for k in d:
            mod, attr = d[k].rsplit('.', 1)
            res[k] = getattr(importlib.import_module(mod), attr)
            ldict.setdefault(k, res[k])
    except ImportError:
        pass
    return res


class BaseSlimLoader(object):
    '''
    This class defines the SlimLoader() interface and provides a base behavior 
    set based upon mutagen.
    '''
    file_mapping = {}
    def __init__(self, filename):
        self.obj = self.file_mapping[get_ext(filename)](filename)
        self.filename = filename
    
    def __iter__(self):
        return iter(self.obj)
    def __getitem__(self, key):
        return self.obj[key]
    def __delitem__(self, key):
        del self.obj[key]
    def __setitem__(self, key, value):
        self.obj[key] = value
    def __contains__(self, key):
        return key in self.obj
    
    def set(self, key, value):
        self.obj.set(key, value)
    def setdefault(self, key, default=None):
        self.obj.setdefault(key, default)
    def get(self, key, default=None):
        return self.obj.get(key, default)
    def keys(self):
        return self.obj.keys()
    def values(self):
        return self.obj.values()
    def items(self):
        return self.obj.items()
    has_key = __contains__
    
    def clear(self):
        self.obj.clear()
    def pop(self, key):
        return self.obj.pop(key)
    def update(self, other=None, **kw):
        self.obj.update(other, **kw)
    def save(self):
        self.obj.save()


class MutagenLoader(BaseSlimLoader):
    pass

loaders.append(MutagenLoader)


class TagPyLoader(BaseSlimLoader):
    # TODO: Implement!
    pass

loaders.append(TagPyLoader)


class KaaLoader(BaseSlimLoader):
    def __init__(self, filename):
        self.obj = self.file_mapping[get_ext(filename)](open(filename, 'rb'))
    
    def __iter__(self):
        return iter(self.keys())
    
    def values(self):
        return [self.obj[k] for k in self.obj.keys()]
    
    def items(self):
        return zip(self.keys(), self.values())
    
    def update(self, other=None, **kw):
        if other:
            for k in other:
                self.obj[k] = other[k]
        for k in kw:
            self.obj[k] = kw[k]


# Do our loading
MutagenLoader.file_mapping = _loader({
        'mp3': 'mutagen.mp3.MP3', 
        'flac': 'mutagen.flac.FLAC', 
        'ogg': 'mutagen.oggvorbis.Open'})

KaaLoader.file_mapping = _loader({
        'mp3': 'kaa.metadata.audio.mp3.Parser', 
        'ogg': 'kaa.metadata.audio.ogg.Parser'})
