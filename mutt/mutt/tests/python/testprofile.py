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
                                   stderr=subpocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.code
