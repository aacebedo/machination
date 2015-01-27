import argparse
import logging
import os

import random
import socket
import fcntl
import struct
import array
import sys
import copy
import getpass

from logging import StreamHandler
from platform import architecture

from core import *
from enums import *
from registries import *
from helpers import *

def make_action(functionToCall):
    class customAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            setattr(args, self.dest, values)
            functionToCall(args)
    
    return customAction

class CmdLine:
    parser = None
    logger = None
    instanceReg = RegistryManager.loadRegistry()            
    templateReg = MachineTemplateRegistry()
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="Machination", description='Machination utility, easily instantiate vagrant based machines.')
        rootSubparsers = self.parser.add_subparsers(help='List available machines')
        
        listParser = rootSubparsers.add_parser('list', help='List elements')
        listSubparsers = listParser.add_subparsers(help='List elements')
        
        templateSubparser = listSubparsers.add_parser('templates', help='List templates')
        templateSubparser.add_argument('provisioner', choices=['ansible','test'], nargs='*', default='ansible', help="List templates of a provider", action=make_action(self.listTemplate))
        #templateSubparser.set_defaults(func=listTemplates)
        
        instanceSubparser = listSubparsers.add_parser('instances', help='List instances')
        #instanceSubparser.set_defaults(func=listInstances)
        
        createParser = rootSubparsers.add_parser('create', help='Create the given machine in the path')
        createParser.add_argument('template', help='Name of the template to create')
        createParser.add_argument('name', help='Name of the machine to create')
        createParser.add_argument('path', help='Path where to create the machine')
        # createParser.add_argument('provisioner', choices=['ansible'], nargs='?', default='ansible', help="List templates of a provider")
        #createParser.set_defaults(func=createMachine)
        
        destroyParser = rootSubparsers.add_parser('destroy', help='Destroy the given machine in the path')
        destroyParser.add_argument('name', help='Name of the machine to destroy')
        #destroyParser.set_defaults(func=destroyMachine)
        
        startParser = rootSubparsers.add_parser('start', help='Start the given machine')
        startParser.add_argument('name', help='Name of the machine to start')
        #startParser.set_defaults(func=startMachine)
        
        stopParser = rootSubparsers.add_parser('stop', help='Stop the given machine')
        stopParser.add_argument('name', help='Name of the machine to stop')
        #stopParser.set_defaults(func=stopMachine)
        
        sshParser = rootSubparsers.add_parser('destroy', help='SSH to the given machine')
        sshParser.add_argument('name', help='Name of the machine to ssh in')
        #sshParser.set_defaults(func=sshMachine)
        

        

    def listTemplate(self, args):
        self.logger = logging.getLogger("test")
        self.logger.debug("toto")
        data = {'name': [], 'version': [], 'path': [], 'provisioner': []}
        templates = self.templateReg.getTemplates();

        for f in templates.values():    
            data['name'].append(f.getName())
            data['version'].append('1.0')
            data['path'].append(os.path.abspath(f.getPath()))
            data['provisioner'].append("ansible")
            
        name_col_width = max(len(word) for word in data['name']) + len("Name") + 2 
        version_col_width = max(len(word) for word in data['version']) + len("Version") + 2
        path_col_width = max(len(word) for word in data['path']) + len("Path") + 2
        pro_col_width = max(len(word) for word in data['provisioner']) + len("Provisioner") + 2
       
        self.logger.info("Name".ljust(name_col_width) + "Version".ljust(version_col_width) + "Path".ljust(path_col_width) + "Provisioner".ljust(pro_col_width))
       
        for row in range(0, len(data['name'])):
            print data['name'][row].ljust(name_col_width) + data['version'][row].ljust(version_col_width) + data['path'][row].ljust(path_col_width) + data['provisioner'][row].ljust(pro_col_width)
             
    def listInstances(self,args):        
        print os.getenv("SUDO_USER")
        
        logger.debug("List instances")
        data = {'name': [], 'path': []}
              
        for i in registry.getInstanceReferences():
            iDetail = registry.loadInstanceDetail(i)
            data['name'].append(iDetail.getName())
            data['path'].append(iDetail.getPath())
            
        name_col_width = max(len(word) for word in data['name']) + len("Name") + 2 
        path_col_width = max(len(word) for word in data['path']) + len("Path") + 2
          
        logger.info("Name".ljust(name_col_width) + "Path".ljust(path_col_width))
        for row in range(0, len(data['name'])):
            print data['name'][row].ljust(name_col_width) + data['path'][row].ljust(path_col_width)
        
        
    def createMachine(self,args):
        logger.debug("Create machine " + args.name + " from template " + args.template + " in " + args.path)
        availableMachines = registry.getTemplates()
        instance = None
            
        if args.name in availableMachines.keys():
            template = availableMachines[args.name]
            logger.debug("Creating ")
               
            hostInterface = template.getHostInterface()
            guestInterfaces = copy.deepcopy(template.getGuestInterfaces())
            arch = template.getArchs()[0]
            provider = template.getProviders()[0]   
            provisioner = template.getProvisioners()[0]
                
            if template.getHostInterface() == None:
                v = raw_input("Please enter the host interface [eth0]: ")
                if not v == "":
                    hostinterface = v
                else:
                    hostinterface = "eth0"
                
            i = 0
            for f in template.getGuestInterfaces():
                v = raw_input("Please enter ipaddress for the interface ["+f.getIPAddr()+"]: ")
                if not v == "":
                    guestInterfaces[i].setIPAddr(v)
                        
                v = raw_input("Please enter macadress for the interface: ["+f.getMACAddr()+"]" )  
                if not v == "":
                    guestInterfaces[i].setMACAddr(v)
                    
                if f.getHostname() != None:
                    v = raw_input("Please enter hostname for the interface: ["+f.getHostname()+"]" )  
                    if not v == "":
                        guestInterfaces[i].setHostname(v)            
                i+=1
                                         
            if len(template.getArchs()) > 1 :
                archs = ""
                for a in template.getArchs():
                    archs += str(a)+", "
               
                v = raw_input("Select an architecture {" + ",".join(map(str,template.getArchs())) + "} [" + arch.name + "]: ")         
                if not v == "":
                    if v in Architecture.__members__.keys():
                        arch = Architecture[v]
                    else:
                        raise InvalidMachineTemplateError("invalid arch")
                     
            if len(template.getProvisioners()) > 1 :
                v = raw_input("Select a provisioner {" + ','.join(map(str,template.getProvisioners())) + "} [" + provisioner + "]: ")
                if v in Provisioner.__members__.keys():
                    provisioner = Provisioner[v]
                else:
                    raise InvalidMachineTemplateError("invalid provisioner")
                    
            if len(template.getProviders()) > 1 :
                v = raw_input("Select a provider  {" + ','.join(map(str,template.getProviders())) + "} [" + provider + "]: ")            
                if v in Provider.__members__.keys():
                    provider = Provider[v]
                else:
                    raise InvalidMachineTemplateError("invalid provisioner")
    
            logger.info("This machine will use the architecture " + str(arch))                                    
            logger.info("This machine will use the provisioner " + str(provisioner))
            logger.info("This machine will use the provider " + str(provider))
            logger.info("This machine use the host interface " + hostinterface)
            i = 0
            logger.info("This machine will have the following network interfaces :")
            for intf in guestInterfaces:            
                logger.info("\tName: eth" + str(i))            
                logger.info("\tIPAddress: " + intf.getIPAddr())
                logger.info("\tMACAddress: " + intf.getMACAddr())
                if intf.getHostname() != None:
                    logger.info("\tHostname: " + intf.getHostname())
                logger.info("")
                i+=1
            
            absPath = os.path.abspath(args.path)
            instance = MachineInstance(args.name,absPath, template, arch, provider, provisioner, hostInterface, guestInterfaces)        
            registry.addInstanceReference(instance.getPath())
            instance.instantiate()
            RegistryManager.saveRegistry(registry)
        else:
            raise InvalidMachineTemplateError(args.name)
          
    def destroyMachine(self,args):
        logger.debug("Destroy machine " + args.name) 
        
    def startMachine(self,args):
        logger.debug("Start machine " + args.name) 
        
    def stopMachine(self,args):
        logger.debug("Stop machine " + args.name) 
        
    def sshMachine(self,args):
        logger.debug("SSH to machine " + args.name)
        
    def parseArgs(self,args):
        self.parser.parse_args()
        