import logging
from logging import StreamHandler

formatter = logging.Formatter('%(message)s')
strHandler = StreamHandler()
strHandler.setLevel(logging.DEBUG)
strHandler.setFormatter(formatter)

COMMANDLINELOGGER = logging.getLogger("CommandLine")
COMMANDLINELOGGER.setLevel(logging.DEBUG)
COMMANDLINELOGGER.addHandler(strHandler)

MACHINEINSTANCEREGISTRYLOGGER = logging.getLogger("MachineInstanceRegistry")
MACHINEINSTANCEREGISTRYLOGGER.setLevel(logging.DEBUG)
MACHINEINSTANCEREGISTRYLOGGER.addHandler(strHandler)
            
MACHINETEMPLATEREGISTRYLOGGER = logging.getLogger("MachineTemplateRegistry")
MACHINETEMPLATEREGISTRYLOGGER.setLevel(logging.DEBUG)
MACHINETEMPLATEREGISTRYLOGGER.addHandler(strHandler)