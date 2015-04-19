##########################################################################
# Machination
# Copyright (c) 2014, Alexandre ACEBEDO, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
##########################################################################

import yaml
import os
import traceback

from machination.helpers import listPath
from machination.helpers import accepts
from machination.loggers import REGISTRYLOGGER
from machination.constants import MACHINATION_CONFIGFILE_NAME
# ##
# Class representing the set of instances available
# ##
class MachineInstanceRegistry():
  _instanceDirs = None

  # ##
  # Constructor
  # ##
  @accepts(None, list)
  def __init__(self, instanceDirs):
    REGISTRYLOGGER.debug("Template registry initialized.")
    self._instanceDirs = instanceDirs
    REGISTRYLOGGER.debug("Instances are searched in the following directories: {0}".format(', '.join(self._instanceDirs)))

  # ##
  # Function to retrieve the available instances
  # ##
  def getInstances(self):
    _instances = {}
    for d in self._instanceDirs:
      path = listPath(d)
      # For each path to scan
      for iDir in path:
        # Check if the file exists and if there is a VagrantFile and a config file in it
        if os.path.isdir(iDir) and os.path.exists(os.path.join(iDir, "Vagrantfile")) and os.path.exists(os.path.join(iDir, MACHINATION_CONFIGFILE_NAME)):
          try:
            filename = os.path.join(iDir, MACHINATION_CONFIGFILE_NAME)
            openedFile = open(filename, "r")
            instance = yaml.load(openedFile)
            _instances[instance.getName()] = instance
            REGISTRYLOGGER.debug("Instance stored in '{0}' loaded".format(filename))
            
          except Exception as e:
            REGISTRYLOGGER.error("Unable to load instance stored in '{0}': {1}".format(iDir, str(e)))
            REGISTRYLOGGER.debug(traceback.format_exc())
    return _instances

# ##
# Class to retrieve the available templates
# ##
class MachineTemplateRegistry():
    _templateDirs = None
    # ##
    # Constructor
    # ##
    @accepts(None, list)
    def __init__(self, templateDirs):
      self._templateDirs = templateDirs
      REGISTRYLOGGER.debug("Templates are searched in the following directories: {0}".format(','.join(self._templateDirs)))

    def getTemplates(self):
      machineTemplates = {}
      for d in self._templateDirs:
        files = listPath(d)
        for f in files:
          if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".template":
            try:
              openedFile = open(os.path.join(f), "r")
              template = yaml.load(openedFile)
              machineTemplates["{0}:{1}".format(template.getName(),template.getVersion())] = template
              REGISTRYLOGGER.debug("Template stored in '{0}' loaded".format(f))
            except Exception as e:
              REGISTRYLOGGER.warning("Unable to load template stored in '{0}: {1}".format(f,str(e)))
              REGISTRYLOGGER.debug(traceback.format_exc())
      return machineTemplates
