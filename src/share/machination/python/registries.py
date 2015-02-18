import yaml
import os
from logging import *
from core import MachineTemplate
from helpers import *
from constants import *

class MachineInstanceRegistry():
    logger = None
    instanceDir = None
    
    def __init__(self,instanceDir):
        self.instanceDir = instanceDir
        
    def getInstances(self):
        path = listPath(self.instanceDir)
        instances = {}
        for d in path:
            if os.path.isdir(d) and os.path.exists(os.path.join(d,"Vagrantfile")) and os.path.exists(os.path.join(d,"config.yml")) :                
                file = open(os.path.join(d,"config.yml"),"r")               
                instance = yaml.load(file)             
                if instance != None:
                    instances[instance.getName()] = instance
        return instances

class MachineTemplateRegistry():
    logger = None
    templateDirs = None
    
    def __init__(self,templateDirs):
        self.templateDirs = templateDirs
        
    def getTemplates(self):
        machineTemplates = {}
        for d in self.templateDirs:
            files = listPath(d)
            for f in files:
                if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                    file = open(os.path.join(f),"r")
                    machine = yaml.load(file)
                    print(machine.getName() +" "+ str(machine.getArchs()))
                    machineTemplates[machine.getName()] = machine 
        return machineTemplates
