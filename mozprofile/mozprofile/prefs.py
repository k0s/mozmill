#!/usr/bin/env python

"""
user preferences
"""

import os
from ConfigParser import SafeConfigParser as ConfigParser

try:
    import json
except ImportError:
    import simplejson as json

class PreferencesReadError(Exception):
    """read error for prefrences files"""

class Preferences(object):
    def __init__(self, prefs):
        self._prefs = []

    def add(self, prefs):
        # wants a list of 2-tuples
        if isinstance(prefs, dict):
            prefs = dict.items()
        self._prefs += prefs

    @classmethod
    def read(cls, path):
        """read preferences from a file"""

        section = None # for .ini files
        basename = os.path.basename(path) 
        if ':' in basename:
            # section of INI file
            path, section = path.rsplit(':', 1)

        if not os.path.exists(path):
            raise PreferencesReadError("'%s' does not exist" % path)

        if section:
            try:
                return cls.read_ini(path, section)
            except PreferencesReadError:
                raise
            except Exception, e:
                raise PreferencesReadError(str(e))

        # try both JSON and .ini format

    @classmethod
    def read_ini(cls, path, section=None):
        parser = ConfigParser()
        parser.read(path)

        if section:
            if section not in parser.sections():
                raise PreferencesReadError("No section '%s' in %s" % (section, path))
        else:
            return parser.defaults()

    @classmethod
    def read_json(cls, path):
        prefs = json.loads(file(path).read())
        if type(prefs) not in [list, dict]:
            raise PreferencesReadError("Malformed preferences: %s" % path)
        if isinstance(prefs, list):
            if [i for i in prefs if type(i) != list or len(i) != 2]:
                raise PreferencesReadError("Malformed preferences: %s" % path)
            values = [i[1] for i in prefs]
        elif isinstance(prefs, dict):
            values = prefs.values()
        else:
            raise PreferencesReadError("Malformed preferences: %s" % path)
        types = (bool, basestring, int)
        if [i for i in values
            if not [isinstance(i, j) for j in types]]:
            pass

if __name__ == '__main__':
    pass
