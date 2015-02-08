import os

MACHINATION_INSTALLDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..")
MACHINATION_WORKDIR = os.path.join(os.path.expanduser("~"),".machination")
MACHINATION_INSTANCESDIR = os.path.join(MACHINATION_WORKDIR,"instances")
