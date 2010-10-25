#!/usr/bin/env python

"""
example of invocation of python event handlers using the API
"""

import os
from mozmill import create_mozmill

dirname = os.path.abspath(os.path.dirname(__file__))
test = os.path.join(dirname, 'test_event_handler.py')

class MyEventHandler(object):
  """example event handler"""
  
  def __init__(self):
    self._events = []
    self.ended = False

  def __call__(self, eventName, obj):
    self._events.append(eventName)

  def events(self):
    return {'mozmill.endRunner': self.endRunner}

  def endRunner(self, obj):
    self.ended = True


def test_event_handler():

  assert os.path.exists(test)
  
  handler = MyEventHandler()
  mozmill = create_mozmill('firefox', handlers=(handler,))
  mozmill.run(test)
  expected = [u'register', u'mozmill.startRunner', u'mozmill.setModule', u'mozmill.persist', u'mozmill.endRunner']
  assert handler._events == expected
  assert handler.ended

if __name__ == '__main__':
  test_event_handler()
