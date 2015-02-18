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
import logging
from core import MachineTemplate
from helpers import *
from constants import *

class MachineInstanceRegistry():
    logger = None
    instanceDir = None
    
    def __init__(self,instanceDir):
        self.logger = logging.getLogger("MachineInstanceRegistry")        
        self.instanceDir = instanceDir
        
    def getInstances(self):
        path = listPath(self.instanceDir)
        instances = {}
        for d in path:
            if os.path.isdir(d) and os.path.exists(os.path.join(d,"Vagrantfile")) and os.path.exists(os.path.join(d,"config.yml")) :                
                file = open(os.path.join(d,"config.yml"),"r")
                try:
                    print(file)
                    instance = yaml.load(file)             
                    if instance != None:
                        instances[instance.getName()] = instance
                except:                    
                    self.logger.warning("Invalid machine instance "+os.path.basename(d));                           
        return instances

class MachineTemplateRegistry():
    logger = None
    templateDirs = None
    
    def __init__(self,templateDirs):
        self.logger = logging.getLogger("MachineTemplateRegistry")
        self.templateDirs = templateDirs
        
    def getTemplates(self):
        machineTemplates = {}
        for d in self.templateDirs:
            files = listPath(d)
            for f in files:
                if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                    file = open(os.path.join(f),"r")
                    try:
                        machine = yaml.load(file)
                        if machine != None:
                            machineTemplates[machine.getName()] = machine
                    except:
                        self.logger.warning("Invalid machine template "+f);
                   
        return machineTemplates
