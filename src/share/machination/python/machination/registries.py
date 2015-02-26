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

from machination.helpers import listPath
from machination.helpers import accepts
from machination.loggers import REGISTRYLOGGER
import machination.core

###
# Class representing the set of instances available
###
class MachineInstanceRegistry():
    instanceDirs = None

    ###
    # Constructor
    ###
    @accepts(None,list)
    def __init__(self,instanceDirs):
        self.instanceDirs = instanceDirs

    ###
    # Function to retrieve the available instances
    ###
    def getInstances(self):

        instances = {}
        for d in self.instanceDirs:
            path = listPath(d)
            # For each path to scan
            for iDir in path:
                # Check if the file exists and if there is a VagrantFile and a config file in it
                if os.path.isdir(iDir) and os.path.exists(os.path.join(iDir,"Vagrantfile")) and os.path.exists(os.path.join(iDir,"config.yml")):
                    try:
                        openedFile = open(os.path.join(iDir,"config.yml"),"r")
                        instance = yaml.load(openedFile)
                        if instance != None:
                            instances[instance.getName()] = instance
                    except:
                        REGISTRYLOGGER.error("Unable to load instance from {0}".format(iDir))
        return instances

###
# Class to retrieve the available templates
###
class MachineTemplateRegistry():
    templateDirs = None

    ###
    # Constructor
    ###
    @accepts(None,list)
    def __init__(self,templateDirs):
        self.templateDirs = templateDirs

    def getTemplates(self):
        machineTemplates = {}
        for d in self.templateDirs:
            files = listPath(d)
            for f in files:
                if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".template":
                    openedFile = open(os.path.join(f),"r")
                    template = yaml.load(openedFile)
                    if template != None and type(template) is machination.core.MachineTemplate:
                        machineTemplates[template.getName()] = template
                    else:
                        REGISTRYLOGGER.warning("Skipped invalid template: {0}".format(f))
        return machineTemplates
