import logging
from logging import StreamHandler

formatter = logging.Formatter('%(message)s')
strHandler = StreamHandler()
strHandler.setLevel(logging.DEBUG)
strHandler.setFormatter(formatter)

COMMANDLINELOGGER = logging.getLogger("CommandLine")
COMMANDLINELOGGER.setLevel(logging.DEBUG)
COMMANDLINELOGGER.addHandler(strHandler)

REGISTRYLOGGER = logging.getLogger("Registries")
REGISTRYLOGGER.setLevel(logging.DEBUG)
REGISTRYLOGGER.addHandler(strHandler)
