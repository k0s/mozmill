#!/usr/bin/env python

import os
import shutil
import tempfile
import unittest
from mozprofile.permissions import PermissionsManager

class ServerLocationsTest(unittest.TestCase):
    """test server locations"""

    locations = """
# This is the primary location from which tests run.
#
http://mochi.test:8888   primary,privileged
    
# a few test locations
http://127.0.0.1:80               privileged
http://127.0.0.1:8888             privileged
http://test:80                    privileged
http://mochi.test:8888            privileged
http://example.org:80                privileged
http://test1.example.org:80          privileged

    """

    def test_server_locations(self):

        # make a permissions manager
        # needs a pointless temporary directory for now
        tempdir = tempfile.mkdtemp()
        permissions = PermissionsManager(tempdir)

        # write a permissions file
        fd, filename = tempfile.mkstemp()
        os.write(fd, self.locations)
        os.close(fd)

        locations = permissions.read_locations(filename)

        # cleanup
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    unittest.main()
