#!/usr/bin/env python

import os
import prefs
import shutil
import subprocess
import unittest

class ProfileTest(unittest.TestCase):
    """test mozprofile"""

    def run_command(self, *args):
        """
        runs mozprofile;
        returns (stdout, stderr, code)
        """
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.strip()
        stderr = stderr.strip()
        return stdout, stderr, process.returncode

    def compare_generated(self, _prefs):
        """
        writes out to a new profile with mozprofile command line
        reads the generated preferences with prefs.py
        compares the results
        cleans up
        """
        commandline = ["mozprofile"]
        for pref, value in _prefs.items():
            commandline += ["--pref", "%s:%s" % (pref, value)]
        profile, stderr, code = self.run_command(*commandline)
        prefs_file = os.path.join(profile, 'user.js')
        self.assertTrue(os.path.exists(prefs_file))
        read = prefs.read(prefs_file)
        self.assertEqual(_prefs, read)
        shutil.rmtree(profile)

    def test_basic_prefs(self):
        _prefs = {"browser.startup.homepage": "http://planet.mozilla.org/"}
        

if __name__ == '__main__':
    unittest.main()
