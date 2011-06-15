#!/usr/bin/env python

import prefs
import subprocess
import unittest

class ProfileTest(unittest.TestCase):
    """test mozprofile"""

    def run(self, *args):
        """
        runs mozprofile;
        returns (stdout, stderr, code)
        """
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode

    def test_basic_prefs(self):
        prefs = {"browser.startup.homepage": "http://planet.mozilla.org/"}
        
        commandline = ["mozprofile"]
        for pref, value in prefs.items():
            commandline += ["--pref", "%s:%s" % (pref, value)]
        profile, stderr, code = self.run(*commandline)
        self.assertEqual(code, 0)

if __name__ == '__main__':
    unittest.main()
