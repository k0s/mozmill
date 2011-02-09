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

import os
import socket
import sys
import traceback

import jsbridge
import manifestparser
import mozrunner
import mozprofile
import handlers

from jsbridge.network import JSBridgeDisconnectError
from datetime import datetime, timedelta
from time import sleep

# metadata
basedir = os.path.abspath(os.path.dirname(__file__))
extension_path = os.path.join(basedir, 'extension')
mozmillModuleJs = "Components.utils.import('resource://mozmill/modules/mozmill.js')"

class TestsFailedException(Exception):
    """exception to be raised when the tests fail"""
    # XXX unused

class TestResults(object):
    """
    accumulate test results for Mozmill
    """
    def __init__(self):

        # test statistics
        self.passes = []
        self.fails = []
        self.skipped = []
        self.alltests = []

        # total test run time
        # TODO: these endpoints are a bit vague as to where they live
        self.starttime = datetime.now()
        self.endtime = None

    def events(self):
        """events the MozMill class will dispatch to"""
        return {'mozmill.endTest': self.endTest_listener}

    def stop(self, handlers, fatal=False):
        """do final reporting and such"""
        self.endtime = datetime.utcnow()

        # handle stop events
        for handler in handlers:
            if hasattr(handler, 'stop'):
                handler.stop(self, fatal)

    ### event listener

    def endTest_listener(self, test):
        self.alltests.append(test)
        if test.get('skipped', False):
            self.skipped.append(test)
        elif test['failed'] > 0:
            self.fails.append(test)
        else:
            self.passes.append(test)


class MozMill(object):
    """
    MozMill is a test runner  You should use MozMill as follows:

    m = MozMill(...)
    m.run(tests)
    m.stop()
    """

    def __init__(self, runner, results, jsbridge_port=24242, jsbridge_timeout=60, handlers=()):
        """
        - runner : a MozRunner instance to run the app
        - results : a TestResults instance to accumulate results
        - jsbridge_port : port jsbridge uses to connect to to the application
        - jsbridge_timeout : how long to go without jsbridge communication
        - handlers : pluggable event handler
        """

        # the MozRunner
        self.runner = runner

        # mozmill puts your data here
        self.results = results 

        # queue of tests
        self.test_queue = []

        # jsbridge parameters
        self.jsbridge_port = jsbridge_port
        self.jsbridge_timeout = jsbridge_timeout

        # persisted data
        self.persisted = {}

        # shutdown parameters
        self.shutdownModes = enum('default', 'user_shutdown', 'user_restart')
        self.currentShutdownMode = self.shutdownModes.default
        self.userShutdownEnabled = False
        self.endRunnerCalled = False

        # setup event listeners
        self.global_listeners = []
        self.listeners = []
        self.add_listener(self.persist_listener, eventType="mozmill.persist")
        self.add_listener(self.endRunner_listener, eventType='mozmill.endRunner')
        self.add_listener(self.startTest_listener, eventType='mozmill.setTest')
        self.add_listener(self.userShutdown_listener, eventType='mozmill.userShutdown')

        # add listeners for event handlers
        self.handlers = [results]
        self.handlers.extend(handlers)
        for handler in self.handlers:
            for event, method in handler.events().items():
                self.add_listener(method, eventType=event)
            if hasattr(handler, '__call__'):
                self.add_global_listener(handler)

        # disable the crashreporter
        os.environ['MOZ_CRASHREPORTER_NO_REPORT'] = '1'

    ### methods for event listeners

    def add_listener(self, callback, **kwargs):
        self.listeners.append((callback, kwargs,))

    def add_global_listener(self, callback):
        self.global_listeners.append(callback)

    def persist_listener(self, obj):
        self.persisted = obj

    def startTest_listener(self, test):
        self.current_test = test

    def endRunner_listener(self, obj):
        self.endRunnerCalled = True
        
    def userShutdown_listener(self, obj):
        if obj in [self.shutdownModes.default, self.shutdownModes.user_restart, self.shutdownModes.user_shutdown]:
            self.currentShutdownMode = obj
        self.userShutdownEnabled = not self.userShutdownEnabled        

    ### methods for startup

    def create_network(self):

        # get the bridge and the back-channel
        self.back_channel, self.bridge = jsbridge.wait_and_create_network("127.0.0.1",
                                                                          self.jsbridge_port)

        # set a timeout on jsbridge actions in order to ensure termination
        # XXX bad touch
        self.back_channel.timeout = self.bridge.timeout = self.jsbridge_timeout
        
        # Assign listeners to the back channel
        for listener in self.listeners:
            self.back_channel.add_listener(listener[0], **listener[1])
        for global_listener in self.global_listeners:
            self.back_channel.add_global_listener(global_listener)

    def start_runner(self):
        """start the MozRunner"""

        # if user_restart we don't need to start the browser back up
        if self.currentShutdownMode != self.shutdownModes.user_restart:
            self.runner.start()

        # create the network
        self.create_network()

        # fetch the application info
        # XXX we do this per start_runner, but really it should either
        # be done once or stored separately per start_runner instance
        # its better, hypothetically, to store per runner, as if the
        # appinfo changes (e.g. on upgrade) you could discriminate
        # vs that
        self.results.appinfo = self.get_appinfo(self.bridge)

        frame = jsbridge.JSObject(self.bridge,
                                  "Components.utils.import('resource://mozmill/modules/frame.js')")

        # set some state
        self.endRunnerCalled = False # transfer persisted data
        frame.persisted = self.persisted

        # return the frame
        return frame

    def run_tests(self):
        """run test files"""

        if not self.test_queue:
            return # nothing to do

        # start the runner
        frame = self.start_runner()
        
        # run tests
        while self.test_queue:
            test = self.test_queue.pop(0)
            frame.runTestFile(test['path'])
            self.currentShutdownMode = self.shutdownModes.default
            
        while not self.endRunnerCalled:
            # XXX could cause infinite loop
            sleep(.25)

        # Give a second for any callbacks to finish.
        sleep(1)

        # stop the runner
        self.stop_runner()

    def run(self, tests):
        """run the tests"""

        self.test_queue.extend(tests)

        disconnected = False
        try:
            self.run_tests()
        except JSBridgeDisconnectError:
            disconnected = True
            if not self.userShutdownEnabled:
                self.report_disconnect()
                raise
            
        if disconnected:
            # raise the disconnect error
            raise

    def get_appinfo(self, bridge):
        """ Collect application specific information """
        mozmill = jsbridge.JSObject(bridge, mozmillModuleJs)
        appInfo = mozmill.appInfo
        results = {'application_id': str(appInfo.ID),
                   'application_name': str(appInfo.name),
                   'application_version': str(appInfo.version),
                   'application_locale': str(mozmill.locale),
                   'platform_buildid': str(appInfo.platformBuildID),
                   'platform_version': str(appInfo.platformVersion),
                  }
        results.update(self.runner.get_repositoryInfo())
        return results

    ### methods for shutting down and cleanup
    
    def report_disconnect(self):
        test = self.current_test
        test['passes'] = []
        test['fails'] = [{
          'exception' : {
            'message': 'Disconnect Error: Application unexpectedly closed'
          }
        }]
        test['passed'] = 0
        test['failed'] = 1

        # send to self.results
        # XXX bad touch
        self.results.alltests.append(test)
        self.results.fails.append(test)

    def stop_runner(self, timeout=30):

        sleep(1)

        # quit the application via JS
        # this *will* cause a diconnect error
        # (not sure what the socket.error is all about)
        try:
            mozmill = jsbridge.JSObject(self.bridge, mozmillModuleJs)
            mozmill.cleanQuit()
        except (socket.error, JSBridgeDisconnectError):
            pass

        # wait for the runner to stop
        starttime = datetime.utcnow()
        self.runner.wait(timeout=timeout)
        endtime = datetime.utcnow()
        if ( endtime - starttime ) > timedelta(seconds=timeout):
            try:
                self.runner.stop()
            except:
                # XXX Not sure why we bare except here :/
                pass

    def stop(self):
        """cleanup and invoking of final handlers"""

        # close the bridge and back channel
        self.back_channel.close()
        self.bridge.close()

        # cleanup 
        if self.runner is not None:
            self.runner.cleanup()


### methods for test collection

def collect_tests(path):
    """find all tests for a given path"""

    path = os.path.abspath(path)
    if os.path.isfile(path):
        return [path]

    files = []
    for filename in sorted(os.listdir(path)):
        if filename.startswith("test"):
            full = os.path.join(path, filename)
            if os.path.isdir(full):
                files += collect_tests(full)
            else:
                files.append(full)
    return files

def collect_restart_tests(path):
    """find all restart tests for a given path"""
    # XXX this method is a bit wonky and magical as
    # far as what it actually does.  just sayin

    path = os.path.abspath(path)
    assert os.path.isdir(path)
    
    test_dirs = [os.path.join(path, d) for d in sorted(os.listdir(path))
                 if d.startswith('test')
                 and os.path.isdir(os.path.join(path, d))]

    # if you find subdirectories, recurse into them
    # otherwise, just take tests from this directory
    # its magic!
    files = []
    if test_dirs:
        for test_dir in test_dirs:
            files += collect_restart_tests(test_dir)
    else:
        counter = 1
        while os.path.isfile(os.path.join(path, 'test%d.js' % counter)):
             files.append(os.path.join(path, 'test%d.js' % counter))
             counter += 1

    return files
        
### command line interface

class CLI(mozrunner.CLI):
    """command line interface to mozmill"""
    
    module = "mozmill"

    def __init__(self, args):

        # add and parse options
        mozrunner.CLI.__init__(self, args)

        # instantiate plugins
        self.event_handlers = []
        for cls in handlers.handlers():
            handler = handlers.instantiate_handler(cls, self.options)
            if handler is not None:
                self.event_handlers.append(handler)

        # read tests from manifests (if any)
        self.manifest = manifestparser.TestManifest(manifests=self.options.manifests)

        # expand user directory and check existence for the test
        for test in self.options.tests:
            test = os.path.expanduser(test)
            if not os.path.exists(test):
                raise Exception("Not a valid test file/directory: %s" % test)

            # collect the tests
            if self.options.restart:
                self.manifest.tests.extend([{'test': os.path.basename(t),
                                             'path': t,
                                             'type': 'restart'}
                                            for t in collect_restart_tests(test)])
            else:
                self.manifest.tests.extend([{'test': os.path.basename(t),
                                             'path': t}
                                            for t in collect_tests(test)])

    def add_options(self, parser):
        mozrunner.CLI.add_options(self, parser)

        parser.add_option("-t", "--test", dest="tests",
                          action='append', default=[],
                          help='Run test')
        parser.add_option("--timeout", dest="timeout", type="float",
                          default=60., 
                          help="seconds before harness timeout if no communication is taking place")
        parser.add_option("--restart", dest='restart', action='store_true',
                          default=False,
                          help="operate in restart mode")
        parser.add_option("-m", "--manifest", dest='manifests', action='append',
                          help='test manifest .ini file')
        parser.add_option('-D', '--debug', dest="debug", 
                          action="store_true",
                          help="debug mode",
                          default=False)
        parser.add_option('-P', '--port', dest="port", type="int",
                          default=24242,
                          help="TCP port to run jsbridge on.")

        for cls in handlers.handlers():
            if hasattr(cls, 'add_options'):
                cls.add_options(parser)

    def profile_args(self):
        """
        return arguments needed to make a profile object from
        this command-line interface
        """
        profile_args = mozrunner.CLI.profile_args(self)
        profile_args['addons'].append(extension_path)
        profile_args['addons'].append(jsbridge.extension_path)

        if self.options.debug:
            profile_args['preferences'] = {
              'extensions.checkCompatibility': False,
              'javascript.options.strict': True
            }
        return profile_args

    def command_args(self):
        """arguments to the application to be run"""
        
        cmdargs = mozrunner.CLI.command_args(self)
        if self.options.debug and '-jsconsole' not in cmdargs:
            cmdargs.append('-jsconsole')
        if '-jsbridge' not in cmdargs:
            cmdargs += ['-jsbridge', '%d' % self.options.port]
        if '-foreground' not in cmdargs:
            cmdargs.append('-foreground')
        return cmdargs
        
    def run(self):

        # groups of tests to run together
        tests = self.manifest.tests[:]
        test_groups = [[]] 
        while tests:
            test = tests.pop(0)
            if test.get('type') == 'restart':
                test_groups.append([test])
                test_groups.append([]) # make a new group for non-restart tests
                continue
            test_groups[-1].append(test)
        test_groups = [i for i in test_groups if i] # filter out empty groups

        # make sure you have tests to run
        if not test_groups:
            self.parser.error("No tests found. Please specify tests with -t or -m")
        
        # create a place to put results
        results = TestResults()
        
        # create a Mozrunner
        runner = self.create_runner()

        # create a MozMill
        mozmill = MozMill(runner, results,
                          jsbridge_port=self.options.port,
                          jsbridge_timeout=self.options.timeout,
                          handlers=self.event_handlers
                          )

        # run the tests
        exception = None # runtime exception
        try:
            for test_group in test_groups:
                mozmill.run(test_group)
        except:
            exception_type, exception, tb = sys.exc_info()

        # shutdown the test harness cleanly
        mozmill.stop()

        # do whatever reporting you're going to do
        results.stop(self.event_handlers)

        # exit on bad stuff happen
        if exception:
            traceback.print_exception(exception_type, exception, tb)
        if exception or results.fails:
            sys.exit(1)

        # return results on success [currently unused]
        return results
        

def enum(*sequential, **named):
    # XXX to deprecate
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def cli(args=sys.argv[1:]):
    CLI(args).run()

if __name__ == '__main__':
    cli()
