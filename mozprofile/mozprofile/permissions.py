#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozprofile.
#
# The Initial Developer of the Original Code is
# Mozilla Corporation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#  Joel Maher <joel.maher@gmail.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****


"""
add permissions to the profile
"""

import os
import codecs
import sqlite3
import itertools

class SyntaxError(Exception):
    "Signifies a syntax error on a particular line in server-locations.txt."

    def __init__(self, lineno, msg = None):
        self.lineno = lineno
        self.msg = msg

    def __str__(self):
        s = "Syntax error on line " + str(self.lineno)
        if self.msg:
            s += ": %s." % self.msg
        else:
            s += "."
        return s


class Location(object):
    "Represents a location line in server-locations.txt."

    attrs = ('scheme', 'host', 'port')

    def __init__(self, scheme, host, port, options):
        for attr in self.attrs:
            setattr(self, attr, locals()[attr])
        self.options = options

    def isEqual(self, location):
        "compare scheme/host/port, but ignore options"
        return len([i for i in self.attrs if getattr(self, i) == getattr(location, i)]) == len(self.attrs)


class PermissionsManager(object):
    _num_permissions = 0

    def __init__(self, profileDir, locations=None):
        self._profileDir = profileDir
        self._locations = []
        if locations:
            if type(locations) is list:
                for l in locations:
                    self.add_hostdict(l)
            elif type(locations) is dict:
                self.add_hostdict(locations)
            elif os.path.exists(locations):
                self.add_file(locations)

    def write_permission(self, location):
        # Open database and create table
        permDB = sqlite3.connect(os.path.join(self._profileDir, "permissions.sqlite"))
        cursor = permDB.cursor();
        # SQL copied from nsPermissionManager.cpp
        cursor.execute("""CREATE TABLE IF NOT EXISTS moz_hosts (
           id INTEGER PRIMARY KEY,
           host TEXT,
           type TEXT,
           permission INTEGER,
           expireType INTEGER,
           expireTime INTEGER)""")

        permissions = {'allowXULXBL':[(location.host, 'noxul' not in location.options)]}

        for perm in permissions.keys():
          for host,allow in permissions[perm]:
            self._num_permissions += 1
            cursor.execute("INSERT INTO moz_hosts values(?, ?, ?, ?, 0, 0)",
                           (self._num_permissions, host, perm, 1 if allow else 2))

        # Commit and close
        permDB.commit()
        cursor.close()

    def add(self, newLocations): # should be *newLocations

        found = False
        for location in newLocations:
            for loc in self._locations:
                if loc.isEqual(location):
                    found = True

        if not found:
            self._locations.append(location)
            self.write_permission(location)
        else:
            # TODO: print warning here
            pass

    def add_host(self, host='', port='80', scheme='http', options='privileged'):
        locations = self.add([Location(scheme, host, port, options)])
        self.add(locations)

    def add_hostdict(self, location):
        locations = []
        if (not 'scheme' in location):
            location['scheme'] = 'http'
        if (not 'port' in location):
            location['port'] = '80'
        if (not 'options' in location):
            location['options'] = 'privileged'

        locations.append(Location(location['scheme'], location['host'], location['port'], location['options']))
        self.add(locations)

    def add_file(self, path):
        """add permissions from a locations file """
        path = os.path.abspath(path)
        if (os.path.exists(path)):
            self.add(self.read_locations(path))
        else:
            #TODO: warning/error here
            pass

    def read_locations(self, filename):
        """
            Reads the file (in the format of server-locations.txt) and add all 
            valid locations to the self.locations array.

            This is a copy from mozilla-central/build/automation.py.in
            format: mozilla-central/build/pgo/server-locations.txt
        """

        locationFile = codecs.open(locationsPath, "r", "UTF-8")

        # Perhaps more detail than necessary, but it's the easiest way to make sure
        # we get exactly the format we want.  See server-locations.txt for the exact
        # format guaranteed here.
        lineRe = re.compile(r"^(?P<scheme>[a-z][-a-z0-9+.]*)"
                      r"://"
                      r"(?P<host>"
                        r"\d+\.\d+\.\d+\.\d+"
                        r"|"
                        r"(?:[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.)*"
                        r"[a-z](?:[-a-z0-9]*[a-z0-9])?"
                      r")"
                      r":"
                      r"(?P<port>\d+)"
                      r"(?:"
                      r"\s+"
                      r"(?P<options>\S+(?:,\S+)*)"
                      r")?$")
        locations = []
        lineno = 0
        seenPrimary = False
        for line in locationFile:
            lineno += 1
            if line.startswith("#") or line == "\n":
                continue

            match = lineRe.match(line)
            if not match:
                raise SyntaxError(lineno)

            options = match.group("options")
            if options:
                options = options.split(",")

            if "primary" in options:
                if seenPrimary:
                    raise SyntaxError(lineno, "multiple primary locations")
                seenPrimary = True
            else:
                options = []

            locations.append(Location(match.group("scheme"), match.group("host"),
                                      match.group("port"), options))

        if not seenPrimary:
            raise SyntaxError(lineno + 1, "missing primary location")

        return locations

    def getNetworkPreferences(self, proxy = False):
        """ take known locations and generate preferences to handle permissions and proxy """

        # Grant God-power to all the privileged servers on which tests run.
        prefs = {}
        privileged = filter(lambda loc: "privileged" in loc.options, self._locations)
        for (i, l) in itertools.izip(itertools.count(1), privileged):
            prefs.update({"capability.principal.codebase.p%s.granted" % (i): "UniversalPreferencesWrite UniversalXPConnect UniversalPreferencesRead"})

            #TODO: do we need the port?
            prefs.update({"capability.principal.codebase.p%s.id" % (i): "%s" % (l.scheme + "://" + l.host)})
            prefs.update({"capability.principal.codebase.p%s.subjectName" % (i): ""})
            print "added p1 id + subject\n"

        user_prefs = {}
        if (proxy):
            user_prefs.update(self.pacPrefs())

        return prefs, user_prefs

    def pacPrefs(self):
        """
           return preferences for Proxy Auto Config.

           originally taken from mozilla-central/build/automation.py.in
        """

        prefs = {}

        # We need to proxy every server but the primary one.
        origins = ["'%s://%s:%s'" % (l.scheme, l.host, l.port)
                  for l in filter(lambda l: "primary" not in l.options, self._locations)]
        origins = ", ".join(origins)

        #TODO: this is not a reliable way to determine the Proxy host
        for l in self._locations:
            if "primary" in l.options:
                webServer = l.host
                httpPort  = l.port
                sslPort   = 443

        pacURL = """data:text/plain,
function FindProxyForURL(url, host)
{
  var origins = [%(origins)s];
  var regex = new RegExp('^([a-z][-a-z0-9+.]*)' +
                         '://' +
                         '(?:[^/@]*@)?' +
                         '(.*?)' +
                         '(?::(\\\\\\\\d+))?/');
  var matches = regex.exec(url);
  if (!matches)
    return 'DIRECT';
  var isHttp = matches[1] == 'http';
  var isHttps = matches[1] == 'https';
  var isWebSocket = matches[1] == 'ws';
  var isWebSocketSSL = matches[1] == 'wss';
  if (!matches[3])
  {
    if (isHttp | isWebSocket) matches[3] = '80';
    if (isHttps | isWebSocketSSL) matches[3] = '443';
  }
  if (isWebSocket)
    matches[1] = 'http';
  if (isWebSocketSSL)
    matches[1] = 'https';

  var origin = matches[1] + '://' + matches[2] + ':' + matches[3];
  if (origins.indexOf(origin) < 0)
    return 'DIRECT';
  if (isHttp)
    return 'PROXY %(remote)s:%(httpport)s';
  if (isHttps || isWebSocket || isWebSocketSSL)
    return 'PROXY %(remote)s:%(sslport)s';
  return 'DIRECT';
}""" % { "origins": origins,
         "remote":  webServer,
         "httpport":httpPort,
         "sslport": sslPort }
        pacURL = "".join(pacURL.splitlines())

        prefs.update({"network.proxy.type": 2})
        prefs.update({"network.proxy.autoconfig_url": "%s" % (pacURL)})

        return prefs

    def clean_permissions(self):
        """Removed permissions added by mozprofile."""

        # Open database and create table
        permDB = sqlite3.connect(os.path.join(self.profile, "permissions.sqlite"))
        cursor = permDB.cursor();

        #TODO: only delete values that we add, this would require sending in the full permissions object
        cursor.execute("DROP TABLE IF EXISTS moz_hosts");

        # Commit and close
        permDB.commit()
        cursor.close()

if __name__ == '__main__':
    pass
