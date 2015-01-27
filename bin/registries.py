import yaml
import os
import logging
from logging import *
from core import MachineTemplate
from helpers import *
MACHINATION_INSTALLDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..")
MACHINATION_WORKDIR = os.path.join(os.path.expanduser("~"),".machination")

class RegistryManager:
    
    @staticmethod
    def loadRegistry():
        if not os.path.exists(MACHINATION_WORKDIR):
            os.makedirs(MACHINATION_WORKDIR)
        file = open(os.path.join(MACHINATION_WORKDIR,"instance_registry.yml"),"r")
        val = yaml.load(file)        
        file.close()
        return val
        
    @staticmethod
    def saveRegistry(registry):
        if not os.path.exists(MACHINATION_WORKDIR):
            os.makedirs(MACHINATION_WORKDIR)
             
        file = open(os.path.join(MACHINATION_WORKDIR,"instance_registry.yml"),"w+")
        file.write( yaml.dump(registry,default_flow_style=False))
        file.close()

class MachineInstanceRegistry(yaml.YAMLObject):
    yaml_tag = "!MachineInstanceRegistry"
    instances = []
    logger = None
    
    def __init__(self, instances = []):  
        self.instances = instances
    
    def getInstanceReferences(self):
        return self.instances
    
    def addInstanceReference(self,instancePath):
        self.instances.append(instancePath)
        
    def removeInstanceReference(self,instancePath):
        self.instances.remove(instancePath)
        
    def loadInstanceDetail(self,instancePath):
        stream = open(os.path.join(instancePath,"config.yml"))
        instance = yaml.load(stream)
        return instance
        
    @classmethod
    def to_yaml(cls, dumper, data):           
        representation = {
                               "instances" : data.instances,                                                  
                               }
        node = dumper.represent_mapping(data.yaml_tag,representation)    
        return node
    
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node)        
        return MachineInstanceRegistry(representation['instances'])

class MachineTemplateRegistry():
    def getTemplates(self):
        paths = listPath(os.path.join(MACHINATION_INSTALLDIR,'share','machination', 'machines'))
        machineTemplates = {}
        for f in paths:
            if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                machine = MachineTemplate(f)
                machineTemplates[machine.getName()] = machine
        return machineTemplates
