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

class MachineInstanceAlreadyExistsException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)

class MachineInstanceDoNotExistException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)

    
def make_action(functionToCall):
    class customAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            setattr(args, self.dest, values)
            functionToCall(args)
    return customAction

class CmdLine:
    parser = None
    logger = None
    instanceReg = MachineInstanceRegistry()            
    templateReg = MachineTemplateRegistry()
    
    def __init__(self):
        self.logger = logging.getLogger("commandline")
        self.parser = argparse.ArgumentParser(prog="Machination", description='Machination utility, all your appliances belong to us.')
        rootSubparsers = self.parser.add_subparsers(help='Root parser')
        
        listParser = rootSubparsers.add_parser('list', help='List templates and instances')
        listSubparsers = listParser.add_subparsers(help='List templates and instances')
        
        templateSubparser = listSubparsers.add_parser('templates', help='List machine templates')
        templateSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List templates")
        templateSubparser.add_argument('dummy',nargs='?', help=argparse.SUPPRESS, action=make_action(self.listTemplates))

        instanceSubparser = listSubparsers.add_parser('instances', help='List instances')
        instanceSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List instances")
        instanceSubparser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.listInstances))
            
        createParser = rootSubparsers.add_parser('create', help='Create the given machine in the path')
        createParser.add_argument('template', help='Name of the template to create')
        createParser.add_argument('name', help='Name of the machine to create')
        createParser.add_argument('dummy',nargs='?', help=argparse.SUPPRESS,action=make_action(self.createMachine))
        
        destroyParser = rootSubparsers.add_parser('destroy', help='Destroy the given machine in the path')
        destroyParser.add_argument('name', help='Name of the machine to destroy')
        destroyParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.destroyMachine))
        
        startParser = rootSubparsers.add_parser('start', help='Start the given machine')
        startParser.add_argument('name', help='Name of the machine to start')
        startParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.startMachine))
        
        stopParser = rootSubparsers.add_parser('stop', help='Stop the given machine')
        stopParser.add_argument('name', help='Name of the machine to stop')
        stopParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.stopMachine))
        
        sshParser = rootSubparsers.add_parser('ssh', help='SSH to the given machine')
        sshParser.add_argument('name', help='Name of the machine to ssh in')
        sshParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.sshMachine))
        
    def listTemplates(self, args):
        self.logger.debug("Listing machine templates")
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
            self.logger.info(data['name'][row].ljust(name_col_width) + data['version'][row].ljust(version_col_width) + data['path'][row].ljust(path_col_width) + data['provisioner'][row].ljust(pro_col_width))
             
    def listInstances(self,args):                
        self.logger.debug("Listing machine instances")
        data = {'name': []}
        instances = self.instanceReg.getInstances()
        
        for i in instances.values():
            data['name'].append(i.getName())
            
        name_col_width = max(len(word) for word in data['name']) + len("Name") + 2 
        
        self.logger.info("Name".ljust(name_col_width))
        for row in range(0, len(data['name'])):
            print data['name'][row].ljust(name_col_width)
        
        
    def createMachine(self,args):
        self.logger.debug("Creating a new machine instance named " + args.name + " using template " + args.template)
        
        availableMachines = self.templateReg.getTemplates()
        instances = self.instanceReg.getInstances()
        
        if args.name in instances.keys():
            raise MachineInstanceAlreadyExistsException("Machine named " + args.name + " already exists. Change the name of your new machine or delete the existing instance.")
        
        instance = None  
        if args.template in availableMachines.keys():
            template = availableMachines[args.template]
               
            hostInterface = template.getHostInterface()
            guestInterfaces = copy.deepcopy(template.getGuestInterfaces())
            arch = template.getArchs()[0]
            provider = template.getProviders()[0]   
            provisioner = template.getProvisioners()[0]
            
            if template.getHostInterface() == None:
                v = raw_input("Please enter the host interface [eth0]: ")
                if not v == "":
                    hostInterface = v
                
            i = 0
            for f in template.getGuestInterfaces():
                v = raw_input("Please enter an IP address for the interface ["+f.getIPAddr()+"]: ")
                if not v == "":
                    guestInterfaces[i].setIPAddr(v)
                        
                v = raw_input("Please enter a MAC address for the interface: ["+f.getMACAddr()+"]" )  
                if not v == "":
                    guestInterfaces[i].setMACAddr(v)
                    
                if f.getHostname() != None:
                    v = raw_input("Please enter a hostname for the interface: ["+f.getHostname()+"]" )  
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
                
            self.logger.info("The machine named " + args.name + " will: ")                                    
            self.logger.info("  Use the architecture " + str(arch))                                    
            self.logger.info("  Use the provisioner " + str(provisioner))
            self.logger.info("  Use the provider " + str(provider))
            self.logger.info("  Use the host interface " + hostInterface)
            i = 0
            self.logger.info("  Have the following network interfaces :")
            for intf in guestInterfaces:            
                self.logger.info("    Name: eth" + str(i))            
                self.logger.info("    IPAddress: " + intf.getIPAddr())
                self.logger.info("    MACAddress: " + intf.getMACAddr())
                if intf.getHostname() != None:
                    self.logger.info("    Hostname: " + intf.getHostname())
                self.logger.info("")
                i+=1
            instance = MachineInstance(args.name,template, arch, provider, provisioner, hostInterface, guestInterfaces,[])        
            instance.instantiate()
        else:
            self.logger.error("Unable to instantiate the machine because template named "+ args.template + " cannot be found. Check your template directory.")
            sys.exit(1)
          
    def destroyMachine(self,args):
        self.logger.debug("Destroy machine " + args.name) 
        instances = self.instanceReg.getInstances()        
        if args.name in instances.keys():
            v = raw_input("Are you sure you want to destroy the machine named "+instances[args.name].getName()+". Directory "+instances[args.name].getPath()+") will be destroyed ! [Y/N]: ")            
            if v == "Y" or v == "y":
                instances[args.name].destroy()
            else:
                self.logger.info("Machine not destroyed") 
        else:
            raise MachineInstanceDoNotExistException("Machine named " + args.name + " does not exist.")
        
    def startMachine(self,args):
        self.logger.debug("Start machine " + args.name) 
        instances = self.instanceReg.getInstances()
        if args.name in instances.keys():
            instances[args.name].start()
        else:
            raise MachineInstanceDoNotExistException("Machine named " + args.name + " does not exist.")

    def stopMachine(self,args):
        self.logger.debug("Stop machine " + args.name) 
        instances = self.instanceReg.getInstances()
        
        if args.name in instances.keys():
            instances[args.name].stop()
        else:
            raise MachineInstanceDoNotExistException("Machine named " + args.name + " does not exist.")
        
    def sshMachine(self,args):
        self.logger.debug("SSH to machine " + args.name)
        instances = self.instanceReg.getInstances()
        
        if args.name in instances.keys():
            instances[args.name].ssh()
        else:
            raise MachineInstanceDoNotExistException("Machine named " + args.name + " does not exist.")
        
    def parseArgs(self,args):
        self.parser.parse_args()
        