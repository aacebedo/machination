import logging
from logging import StreamHandler

formatter = logging.Formatter('%(message)s')
strHandler = StreamHandler()
strHandler.setLevel(logging.DEBUG)
strHandler.setFormatter(formatter)

COMMANDLINELOGGER = logging.getLogger("cmdline")
COMMANDLINELOGGER.setLevel(logging.DEBUG)
COMMANDLINELOGGER.addHandler(strHandler)

REGISTRYLOGGER = logging.getLogger("registries")
REGISTRYLOGGER.setLevel(logging.DEBUG)
REGISTRYLOGGER.addHandler(strHandler)

CORELOGGER = logging.getLogger("core")
CORELOGGER.setLevel(logging.DEBUG)
CORELOGGER.addHandler(strHandler)

FILEGENERATORLOGGER = logging.getLogger("filegenerator")
FILEGENERATORLOGGER.setLevel(logging.DEBUG)
FILEGENERATORLOGGER.addHandler(strHandler)

