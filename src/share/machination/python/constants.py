import os

MACHINATION_INSTALLDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..",'..','..'))
MACHINATION_USERDIR = os.path.abspath(os.path.join(os.path.expanduser("~"),".machination"))
MACHINATION_INSTANCESDIR = os.path.join(MACHINATION_USERDIR,"instances")
