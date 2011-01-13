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
# The Original Code is Mozilla Corporation Code.
#
# The Initial Developer of the Original Code is
# Mikeal Rogers.
# Portions created by the Initial Developer are Copyright (C) 2008
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#  Mikeal Rogers <mikeal.rogers@gmail.com>
#  Henrik Skupin <hskupin@mozilla.com>
#  Clint Talbert <ctalbert@mozilla.com>
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
file for interface to transform introspected system information to a format
pallatable to Mozilla

Information:
- os : what operating system ['win', 'mac', 'linux', ...?]
- bits : 32 or 64
- processor : processor architecture ['x86', 'x86_64', 'ppc'
- version : operating system version string
- hostname : name of the local host

For windows, the service pack information is also included
"""

# TODO: it might be a good idea of adding a system name (e.g. 'Ubuntu' for
# linux) to the information; I certainly wouldn't want anyone parsing this
# information and having behaviour depend on it

import os
import platform
import re
import sys

class unknown(object):
    """marker class for unknown information"""
    def __nonzero__(self):
        return False
    def __str__(self):
        return 'UNKNOWN'
unknown = unknown() # singleton

# get system information

info = {'os': unknown,
        'processor': unknown,
        'version': unknown,
        'bits': unknown }

(system, node, release, version, machine, processor) = platform.uname()
(bits, linkage) = platform.architecture()

if system in ["Microsoft", "Windows"]:
    info['os'] = 'win'
    
    # There is a Python bug on Windows to determine platform values
    # http://bugs.python.org/issue7860
    if "PROCESSOR_ARCHITEW6432" in os.environ:
        processor = os.environ.get("PROCESSOR_ARCHITEW6432", processor)
    else:
        processor = os.environ.get('PROCESSOR_ARCHITECTURE', processor)
        system = os.environ.get("OS", system).replace('_', ' ')
        service_pack = os.sys.getwindowsversion()[4]
        info['service_pack'] = service_pack
elif system == "Linux":
    (distro, version, codename) = platform.dist()
    version = distro + " " + version
    if not processor:
        processor = machine
    info['os'] = 'linux'
elif system == "Darwin":
    (release, versioninfo, machine) = platform.mac_ver()
    version = "OS X " + release
    info['os'] = 'mac'
elif sys.platform in ('solaris', 'sunos5'):
    info['os'] = 'unix'
    version = sys.platform

# processor type and bits
if processor in ["i386", "i686"]:
    if bits == "32bit":
        processor = "x86"
    elif bits == "64bit":
        processor = "x86_64"
elif processor == "AMD64":
    bits = "64bit"
    processor = "x86_64"
elif processor == "Power Macintosh":
    processor = "ppc"
bits = re.search('(\d+)bit', bits).group(1)

info.update({'version': version,
             'processor': processor,
             'bits': int(bits),
             'hostname': node,
            })
  
globals().update(info)

choices = {'os': ['linux', 'win', 'mac', 'unix'],
           'bits': [32, 64],
           'processor': ['x86', 'x86_64', 'ppc']}

# exports
__all__ = info.keys()
__all__ += ['info', 'unknown', 'main', 'choices']

def main(args=None):
    from optparse import OptionParser
    parser = OptionParser()
    for key in choices:
        parser.add_option('--%s' % key, dest=key,
                          action='store_true', default=False,
                          help="display choices for %s" % key)
    options, args = parser.parse_args()
    # XXX currently ignore args

    flag = False
    for key, value in options.__dict__.items():
        if value is True:
            print '%s choices: %s' % (key, ' '.join([str(choice)
                                                     for choice in choices[key]]))
            flag = True
    if flag: return

    for key, value in info.items():
        print '%s: %s' % (key, value)

if __name__ == '__main__':
    main()