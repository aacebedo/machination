import yaml
import os
import logging
from logging import *
from core import MachineTemplate
from helpers import *
from constants import *
# class RegistryManager: 
#     @staticmethod
#     def loadRegistry():
#         if not os.path.exists(MACHINATION_WORKDIR):
#             os.makedirs(MACHINATION_WORKDIR)
#         file = open(os.path.join(MACHINATION_WORKDIR,"instance_registry.yml"),"r")
#         val = yaml.load(file)        
#         file.close()
#         return val
#         
#     @staticmethod
#     def saveRegistry(registry):
#         if not os.path.exists(MACHINATION_WORKDIR):
#             os.makedirs(MACHINATION_WORKDIR)
#              
#         file = open(os.path.join(MACHINATION_WORKDIR,"instance_registry.yml"),"w+")
#         file.write( yaml.dump(registry,default_flow_style=False))
#         file.close()

# class MachineInstanceRegistry(yaml.YAMLObject):
#     yaml_tag = "!MachineInstanceRegistry"
#     instances = []
#     logger = None
#     
#     def __init__(self, instances = []):  
#         self.instances = instances
#     
#     def getInstanceReferences(self):
#         return self.instances
#     
#     def addInstanceReference(self,instancePath):
#         self.instances.append(instancePath)
#         
#     def removeInstanceReference(self,instancePath):
#         self.instances.remove(instancePath)
#         
#     def loadInstanceDetail(self,instancePath):
#         stream = open(os.path.join(instancePath,"config.yml"))
#         instance = yaml.load(stream)
#         return instance
# 
#     def loadInstances(self):
#         path = listPath(os.path.join('~','.machination', 'instances'))
#         instances = {}
#         for d in path:
#             if os.path.isdir(d) and os.path.exists(os.path.join(d,"Vagrantfile")) and os.path.exists(os.path.join(d,"config.yml")) :
#                 val = yaml.load(os.path.exists(os.path.join(d,"config.yml")))
#                 if val != None:
#                     instances.append(val)
#         return instances
#         
#     @classmethod
#     def to_yaml(cls, dumper, data):           
#         representation = {
#                                "instances" : data.instances,                                                  
#                                }
#         node = dumper.represent_mapping(data.yaml_tag,representation)    
#         return node
#     
#     @classmethod
#     def from_yaml(cls, loader, node):
#         representation = loader.construct_mapping(node)        
#         return MachineInstanceRegistry(representation['instances'])

class MachineInstanceRegistry():
    logger = None
    def getInstances(self):
        path = listPath(os.path.join(MACHINATION_WORKDIR, 'instances'))
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
    def getTemplates(self):
        systemPath = listPath(os.path.join(MACHINATION_INSTALLDIR,'share','machination', 'templates'))
        userPath = listPath(os.path.join(MACHINATION_WORKDIR, 'templates'))
        machineTemplates = {}
        for f in systemPath:
            if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                machine = MachineTemplate(f)
                machineTemplates[machine.getName()] = machine
        for f in userPath:
            if os.path.isfile(f) and  os.path.splitext(os.path.basename(f))[1] == ".yml":
                machine = MachineTemplate(f)
                if not machine.getName() in machineTemplates:
                    machineTemplates[machine.getName()] = machine
        return machineTemplates
