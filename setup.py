#! /usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

#############################################################################
### Main setup stuff
#############################################################################

def main():
    
    # perform the setup action
    import pygu
    setup_args = {
        'script_args': sys.argv[1:] if len(sys.argv) > 1 else ['install'],
        'name': "pygu",
        'version': pygu.__version__,
        'description': "Pydsigner's Pygame Utilities - a collection of "
                "handy modules for Pygame.",
        'long_description': "Pydsigner's Pygame Utilities"
                ''' - a collection of handy modules for Pygame.

__init__        --  version info
common          --  shared information, classes, and functions
pyramid         --  an advanced resource loader and several gamestate managers
pms             --  a loader for PMS playlists
pyslim          --  an audio metadata loader frontend for multiple loaders
pygw            --  a  GUI toolkit for pyramid
''',
        'author': "Daniel Foerster/pydsigner",
        'author_email': "pydsigner@gmail.com",
        'packages': ['pygu'],
        'license': 'LGPLv3',
        'url': "http://github.com/pydsigner/pygu",
        'classifiers': [
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python',
        ]}
    setup(**setup_args)

if __name__ == '__main__':
    main()
