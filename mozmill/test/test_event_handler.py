#!/usr/bin/env python

"""
example of invocation of python event handlers using the API
"""

from mozmill import MozMill

class MyEventHandler(object):
  """example event handler"""
  
  def __init__(self):
    self._events = []

  def __call__(self, eventName, obj):
    self._events.append(eventName)

  def events(self):
    pass

def test_event_handler():
  pass
