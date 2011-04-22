#!/usr/bin/env python

"""
illustrate use of mozmill as an API
"""

# you have to have some sort of test
import os
here = os.path.dirname(os.path.abspath(__file__))
tests = [{'path': os.path.join(here, 'test_runnershutdown.js')}]

# now to do our thing: basic run
import mozmill
m = mozmill.MozMill.create()
results = m.run(*tests)
results.stop(())

# there should be four passing tests
passes = 4
assert len(results.passes) == passes, "Wrong number of passes. Expected: %d; You got: %d" % (passes, len(results.passes))
assert len(results.alltests) == passes, "Wrong number of tests. Expected: %d; You got: %d" % (passes, len(results.alltests))

# this is how you use a handler
# let's try the logging handler:
from mozmill.logger import LoggerListener
logger = LoggerListener()
m = mozmill.MozMill.create(results=results, handlers=(logger,))
results = m.run(*tests)
results.stop((logger,))

# now there should be eight
passes *= 2
assert len(results.passes) == passes, "Wrong number of passes. Expected: %d; You got: %d" % (passes, len(results.passes))
assert len(results.alltests) == passes, "Wrong number of tests. Expected: %d; You got: %d" % (passes, len(results.alltests))
