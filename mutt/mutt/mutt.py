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
# The Original Code is Cuddlefish Addons SDK code.
#
# The Initial Developer of the Original Code is
# Atul Varma <avarma@mozilla.com>.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Clint Talbert <cmtalbert@gmail.com>
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

import sys
import os
import re
import optparse
import imp
import unittest

from copy import copy
from manifestparser import TestManifest
from processhandler import ProcessHandler

usage = """
%prog [options] command [command-specific options]

Supported Commands:
  test       - run tests

Internal Commands:
  testjs     - run mozmill js tests
  testpy     - run mozmill python tests
  testall    - test whole environment

Experimental and internal commands and options are not supported and may be
changed or removed in the future.
"""

global_options = [
    (("-v", "--verbose",), dict(dest="verbose",
                                help="enable lots of output",
                                action="store_true",
                                default=False)),
    ]

parser_groups = (
    ("Supported Command-Specific Options", [
        (("-p", "--profiledir",), dict(dest="profiledir",
                                       help="profile directory to pass to app",
                                       metavar=None,
                                       default=None,
                                       cmds=['test', 'testjs', 
                                             'testpy', 'testall'])),
        (("-b", "--binary",), dict(dest="binary",
                                   help="path to app binary",
                                   metavar=None,
                                   default=None,
                                   cmds=['test', 'testjs', 'testpy',
                                         'testall'])),
        (("-a", "--app",), dict(dest="app",
                                help=("app to run: firefox (default), "
                                      "xulrunner, fennec, or thunderbird"),
                                metavar=None,
                                default="firefox",
                                cmds=['test', 'testjs', 'testpy',
                                      'testall'])),
        (("", "--times",), dict(dest="iterations",
                                type="int",
                                help="number of times to run tests",
                                default=1,
                                cmds=['test', 'testjs', 'testpy',
                                      'testall'])),
        (("-f", "--filter",), dict(dest="filter",
                                   help=("only run tests whose filenames "
                                         "match FILTER, a regexp"),
                                   metavar=None,
                                   default=None,
                                   cmds=['test', 'testjs', 'testpy',
                                         'testall'])),
        (("-m", "--manifest",), dict(dest="manifest",
                                       help=("use a specific manifest rather than the "
                                             "default all-tests.ini"),
                                       metavar=None,
                                       default=os.path.join(os.path.dirname(__file__), "tests", "all-tests.ini"),
                                       cmds=['test', 'testjs',
                                             'testpy', 'testall'])),
        (("", "--extra-packages",), dict(dest="extra_packages",
                                         help="extra packages to include, comma-separated. Default is 'None'.",
                                         metavar=None,
                                         default=None,
                                         cmds=['test', 'testjs', 'testpy', 'testall'])),
        ]
     ),

    ("Internal Command-Specific Options", [
        (("", "--addons",), dict(dest="addons",
                                 help=("paths of addons to install, "
                                       "comma-separated"),
                                 metavar=None,
                                 default=None,
                                 cmds=['test', 'run', 'testjs', 'testpy', 'testall'])),
        (("", "--logfile",), dict(dest="logfile",
                                  help="log console output to file",
                                  metavar=None,
                                  default=None,
                                  cmds=['test', 'testjs', 'testpy', 'testall'])),
        # TODO: This should default to true once our memory debugging
        # issues are resolved; see bug 592774.
        (("", "--profile-memory",), dict(dest="profileMemory",
                                         help="profile memory usage (default is False)",
                                         action="store_true",
                                         default=False,
                                         cmds=['test', 'testjs', 'testpy', 'testall'])),
        ]
     ),
    )

# Maximum time we'll wait for tests to finish, in seconds.
TEST_RUN_TIMEOUT = 5 * 60

def parse_args(arguments, global_options, usage, parser_groups, defaults=None):

    # create a parser
    parser = optparse.OptionParser(usage=usage.strip())


    # sort the options so that they print in a nice order
    def name_cmp(option):
        return option[0][-1].lstrip('-')
    global_options.sort(key=name_cmp)

    # add the options
    for names, opts in global_options:
        parser.add_option(*names, **opts)
    for group_name, options in parser_groups:
        group = optparse.OptionGroup(parser, group_name)
        options.sort(key=name_cmp)
        for names, opts in options:
            if 'cmds' in opts:
                cmds = opts['cmds']
                del opts['cmds']
                cmds.sort()
                if not 'help' in opts:
                    opts['help'] = ""
                opts['help'] += " (%s)" % ", ".join(cmds)
            group.add_option(*names, **opts)
        parser.add_option_group(group)

    if defaults:
        parser.set_defaults(**defaults)

    (options, args) = parser.parse_args(args=arguments)

    if len(args) != 1:
        parser.print_help()
        parser.exit()

    return (options, args)

def get_pytests(testdict):
    unittests = []
    for t in testdict:
        path = t['path']
        assert os.path.exists(path)
        modname = os.path.splitext(os.path.basename(path))[0]
        module = imp.load_source(modname, path)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        for test in suite:
            unittests.append(test)
    return unittests

def report(fail, pyresults=None, jsresults=None, options=None):
    if not fail:
        print "All tests were successful.  Ship it!"
        return 0

    # Print the failures
    print "Some tests were unsuccessful."
    print "+" * 75
    if pyresults:
        print "Python Failures:"
        for i in pyresults.failures:
            print "%s\n" % str(i)
        for i in pyresults.errors:
            print "%s\n" % str(i)
    else:
        print "No Python Failures"

    print "=" * 75
    if jsresults:
        print "Javascript Failures:"
        for i in jsresults.failures:
            print "%s\n" % str(i)
    else:
        print "No Javascript Failures"
    
    return 1

def test_all(tests, options):
    fail = False

    pytests = [item for item in tests if item['type'] == 'python']
    jstests = [item for item in tests if item['type'] == 'javascript']
    
    try:
        pyresult = test_all_python(pytests, options)
        if pyresult.failures or pyresult.errors:
            fail = True
    except SystemExit, e:
        fail = (e.code != 0) or fail

    try:
        jsresult = test_all_js(jstests, options)
        if jsresult.failures:
            fail = True
    except SystemExit, e:
        fail = (e.code != 0) or fail

    sys.exit(report(fail, pyresult, jsresult, options))

def test_all_python(tests, options):
    print "Running python tests" 
    unittestlist = get_pytests(tests)
    verbosity = 1
    if options.verbose:
        verbosity = 2
    suite = unittest.TestSuite(unittestlist)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)

def test_all_js(tests, options):
    print "Running JS Tests"
    # We run each test in its own instance since these are harness tests.
    # That just seems safer, no opportunity for cross-talk since
    # we are sorta using the framework to test itself
    results = JSResults()
    for t in tests:

        # get CLI arguments to mozmill
        args = []
        if 'restart' in t:
            args.append('--restart')
        if options.binary:
            args.extend(['-b', options.binary])
        args.append('--console-level=DEBUG')        
        args.append('-t')
        args.append(t['path'])

        # run the test
        proc = ProcessHandler("mozmill", args, os.getcwd())
        proc.run()
        status = proc.waitForFinish(timeout=300)
        results.acquire(t['name'], proc.output)
    return results

class JSResults(object):
    """
    Takes in a standard output log and marshals it into our
    class in an additive fashion.
    TODO: This needs some work.  My thought is to go through what we 
    get back from the test, analyze each line, add the passes to the pass list
    add the failures to the fail list, and the rest to the info list.

    But I'm thinking this really needs to be swapped out for a real log parser
    """

    def __init__(self):
        self.failures = []
        self.passes = []
        self.info = []
        self.text = {}
  
    def acquire(self, testname, buf):
        passre = re.compile("^TEST-PASS.*")
        failre = re.compile("^TEST-UNEXPECTED-FAIL.*")
        tback = re.compile("^Traceback.*")
        excpt = re.compile("^Exception:.*")

        self.text[testname] = []

        for line in buf:
            print line
            if passre.match(line):
                self.passes.append(line)
            elif failre.match(line):
                self.failures.append(line)
            elif tback.match(line):
                self.failures.append(line)
            elif excpt.match(line):
                self.failures.append(line)
            else:
                self.info.append(line)
            self.text[testname].append(line)
                

def run(arguments=sys.argv[1:], defaults=None):

    # parse the command line arguments
    parser_kwargs = dict(arguments=arguments,
                         global_options=global_options,
                         parser_groups=parser_groups,
                         usage=usage,
                         defaults=defaults)
    (options, args) = parse_args(**parser_kwargs)
    command = args[0]

    # Parse the manifests
    mp = TestManifest(manifests=(options.manifest,))

    if command == "testpy":
        results = test_all_python(mp.get(tests=mp.active_tests(), type='python'), options)
        if results.failures or results.errors:
            sys.exit(report(True, results, None, options))
        else:
            sys.exit(report(False))

    elif command == "testjs":
        results = test_all_js(mp.get(tests=mp.active_tests(), type='javascript'), options)
        if results.failures:
            sys.exit(report(True, None, results, options))
        else:
            sys.exit(report(False))
  
    elif command == "testall":
        test_all(mp.active_tests(), options)
        return
    else:
        print "Unknown command"
        sys.exit(1)

if __name__ == '__main__':
    run()
