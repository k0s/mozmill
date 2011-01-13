MozInfo
=======

Throughout mozmill and other mozilla python code, checks for various
platforms are done in many different ways.  The various checks needed
lead to a lot of copy+pasting, leaving the reader to wonder....is this
specific check necessary for (e.g.) an operating system?  Because
information is not consolidated, checks are not done consistently, nor
is it defined what we are checking for.

MozInfo proposes to solve this problem.  The current [beta]
implementation gives five key, values: os, hostname, version, bits,
and processor. (Additionally, the service pack is available on
windows, though probably only for legacy reasons.)

API Usage
---------

MozInfo is a python package.  Downloading the software and running
``python setup.py develop`` will allow you to do ``import mozmill``
from python.


Command Line Usage
------------------

MozInfo comes with a command line, ``mozmill`` which may be used to
diagnose one's current system.

Example output::

 os: linux
 hostname: jhammel-THINK
 version: Ubuntu 10.10
 bits: 32
 processor: x86

Three of these fields, 
