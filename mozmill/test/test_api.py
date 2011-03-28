#!/usr/bin/env python

"""
illustrate use of mozmill as an API
"""

# you have to have some sort of test
import os
here = os.path.dirname(os.path.abspath(__file__))
tests = [{'path': os.path.join(here, 'test_runnershutdown.js')}]

# now to do our thing
import mozmill
runner = mozmill.create_runner()
m = mozmill.MozMill(runner)
results = m.run(tests)
results.stop(())
