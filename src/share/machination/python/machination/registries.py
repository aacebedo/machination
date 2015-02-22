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

class MachineInstanceRegistry():
    instanceDir = None
    
    def __init__(self,instanceDir):
        self.instanceDir = instanceDir
        
    def getInstances(self):
        path = listPath(self.instanceDir)
        instances = {}
        for d in path:            
            if os.path.isdir(d) and os.path.exists(os.path.join(d,"Vagrantfile")) and os.path.exists(os.path.join(d,"config.yml")) :                
                openedFile = open(os.path.join(d,"config.yml"),"r")
                instance = yaml.load(openedFile)             
                if instance != None:
                    instances[instance.getName()] = instance
        return instances

class MachineTemplateRegistry():
    templateDirs = None
    
    def __init__(self,templateDirs):
        self.templateDirs = templateDirs
        
    def getTemplates(self):
        machineTemplates = {}        
        for d in self.templateDirs:
            files = listPath(d)
            for f in files:                
                if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                    openedFile = open(os.path.join(f),"r")
                    machine = yaml.load(openedFile)
                    if machine != None:
                        machineTemplates[machine.getName()] = machine
        return machineTemplates
