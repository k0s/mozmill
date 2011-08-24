#!/usr/bin/env python

import mozmill
import os
import tempfile
import unittest

class TestMozmillPersisted(unittest.TestCase):
    """test persisted object"""

    test = """
    var setupModule = function(module){
    controller = mozmill.getBrowserController();
    }
    
    var test_something = function() {
    persisted.fleem = 2;
    %(shutdown)s
    }
    """

    def make_test(self, shutdown=''):
        """make an example test to run"""
        fd, path = tempfile.mkstemp()
        os.write(fd, self.test % dict(shutdown=shutdown))
        os.close(fd)
        return path

    def test_persisted(self):
        passes = 1
        path = self.make_test()
        m = mozmill.MozMill.create()
        m.persisted['foo'] = 'bar'
        results = m.run(dict(path=path))
        self.assertTrue(len(results.passes) == passes)
        print m.persisted

    def test_persisted_shutdown(self):
        path = self.make_test(shutdown='controller.stopApplication();')
        m = mozmill.MozMill.create()
        m.persisted['foo'] = 'bar'
        results = m.run(dict(path=path))
        print m.persisted
        

if __name__ == '__main__':
    unittest.main()
