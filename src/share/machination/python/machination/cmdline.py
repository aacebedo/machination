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

import argparse
import os
import errno
import traceback
from machination.core import MachineInstance, NetworkInterface
from machination.core import SyncedFolder

from machination.loggers import COMMANDLINELOGGER
from machination.constants import MACHINATION_INSTALLDIR
from machination.constants import MACHINATION_USERDIR
from machination.constants import MACHINATION_USERINSTANCESDIR

from machination.registries import MachineTemplateRegistry
from machination.registries import MachineInstanceRegistry


from machination.questions import RegexedQuestion
from machination.questions import BinaryQuestion
from machination.questions import PathQuestion

from machination.enums import Architecture

###
# Function called by the argument parsing objects
###   
def make_action(functionToCall):
    class customAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            setattr(args, self.dest, values)
            functionToCall(args)
    return customAction

###
# Class used to handle the arguments passed by the command line
###
class CmdLine:
    ###
    # Function used to list available templates
    # Templates are searched in the install directory of machination but also in the user workdir (~/.machination)
    ###
    def listTemplates(self, args):
        res = 0
        # Create the template registry that will list all available template on the machine
        templateReg = MachineTemplateRegistry([os.path.join(MACHINATION_INSTALLDIR,'share','machination', 'templates'),os.path.join(MACHINATION_USERDIR, 'templates') ])
        COMMANDLINELOGGER.debug("Listing machine templates")
        
        try:
            templates = templateReg.getTemplates();
            # Create an array containing a set of informations about the template. 
            # This array will be used to display the information to the user
            data = {'name': [], 'version': [], 'path': [], 'provisioners': [], 'providers': [], 'archs': []}
            for f in templates.values():    
                data['name'].append(f.getName())
                data['version'].append('1.0')
                data['path'].append(os.path.abspath(f.getPath()))
                data['provisioners'].append(",".join(map(str,f.getProvisioners())))
                data['providers'].append(",".join(map(str,f.getProviders())))
                data['archs'].append(",".join(map(str,f.getArchs())))
                
            # Each column width will be computed as the max length of its items
            name_col_width=0
            version_col_width=0
            path_col_width=0
            provisioner_col_width=0
            providers_col_width=0
            archs_col_width=0
            
            # Getting the max for each column
            if len(data['name']) != 0:
                name_col_width = max(len(word) for word in data['name']) + len("Name") + 2 
            if len(data['version']) != 0:        
                version_col_width = max(len(word) for word in data['version']) + len("Version") + 2
            if len(data['path']) != 0:
                path_col_width = max(len(word) for word in data['path']) + len("Path") + 2
            if len(data['provisioners']) != 0:
                provisioner_col_width = max(len(word) for word in data['provisioners']) + len("Provisioners") + 2
            if len(data['providers']) != 0:
                providers_col_width = max(len(word) for word in data['providers']) + len("Providers") + 2
            if len(data['archs']) != 0:
                archs_col_width = max(len(word) for word in data['archs']) + len("Architectures") + 2
            # Display the array
            # Checking number of items in the column name to know if there is something to display or not
            if len(data['name'])!=0:
                # Display the array titles
                COMMANDLINELOGGER.info("Name".ljust(name_col_width) + "Version".ljust(version_col_width) + "Path".ljust(path_col_width) + "Provisioners".ljust(provisioner_col_width)  + "Providers".ljust(providers_col_width)  + "Architectures".ljust(archs_col_width))
                for row in range(0, len(data['name'])):
                    COMMANDLINELOGGER.info(data['name'][row].ljust(name_col_width) + data['version'][row].ljust(version_col_width) + data['path'][row].ljust(path_col_width) + data['provisioners'][row].ljust(provisioner_col_width)  + data['providers'][row].ljust(providers_col_width)  + data['archs'][row].ljust(archs_col_width))
            else:
                COMMANDLINELOGGER.info("No templates available")
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to list templates: {0}".format(str(e)))
            res = errno.EINVAL
        return res

    ###
    # Function to list the instances
    # The instances are searched in the user workdir (~/.machination)
    ###
    def listInstances(self,args):
        res = 0
        COMMANDLINELOGGER.debug("Listing machine instances")
        # Populating the registry of instances
        instanceReg = MachineInstanceRegistry([os.path.join(MACHINATION_USERINSTANCESDIR,'instances')])
        try:
            instances = instanceReg.getInstances()     
            # Create an array to display the available templates
            data = {'name': [],'path': []}
            for i in instances.values():
                data['name'].append(i.getName())
                data['path'].append(i.getPath())
                
            # Display the array of templates
            # Check if there is an item in the resulting array using the length of the column name
            if len(data['name']) != 0:
                name_col_width = max(len(word) for word in data['name']) + len("Name") + 2 
                path_col_width = max(len(word) for word in data['path']) + len("Path") + 2 
                
                COMMANDLINELOGGER.info("Name".ljust(name_col_width)+"Path".ljust(path_col_width))
                for row in range(0, len(data['name'])):
                    COMMANDLINELOGGER.info(data['name'][row].ljust(name_col_width) + data['path'][row].ljust(name_col_width))
            else:
                COMMANDLINELOGGER.info("No instances available")
        except Exception as e:
            print traceback.format_exc()
            COMMANDLINELOGGER.error("Unable to list instances: {0}".format(str(e)))
            res = errno.EINVAL
        return res
            
    ###
    # Function to create a new machine
    ###
    def createMachine(self,args):
        res = 0
        COMMANDLINELOGGER.info("Creating a new machine instance named {0} using template {1}".format(args.name,args.template))
        # Creating the template and instances registries       
        templateReg = MachineTemplateRegistry([os.path.join(MACHINATION_INSTALLDIR,'share','machination', 'templates'),os.path.join(MACHINATION_USERDIR, 'templates')])
        instanceReg = MachineInstanceRegistry(os.path.join(MACHINATION_USERDIR,'instances'))
        
        templates = []
        instances = []
        try:
            # Get templates
            templates = templateReg.getTemplates()
            # Get instances 
            instances = instanceReg.getInstances()
            # Check if the instance is already in the registry
            if args.name not in instances.keys():
                # Check if the requested template exists
                if args.template in templates.keys():
                    template = templates[args.template]
                    guestInterfaces = []
                    arch = template.getArchs()[0]
                    provider = template.getProviders()[0]
                    provisioner = template.getProvisioners()[0]
                    osVersion = template.getOsVersions()[0]
                    syncedFolders = []
                    
                    # Ask for the host interface to use
                    hostInterface = RegexedQuestion("Enter the host interface","[a-z]+[0-9]+","eth0").ask()
                    
                    # If there is more than one architecture available for the template
                    # Ask the user to choose
                    if len(template.getArchs()) > 1 :
                        arch = Architecture.fromString(RegexedQuestion("Select an architecture {"+ ",".join(map(str,template.getArchs())) +"}","[" + ",".join(map(str,template.getArchs())) + "]",arch.name).ask())
                        
                    # If there is more than one OS version available for the template
                    # Ask the user to choose
                    if len(template.getOsVersions()) > 1 :
                        osVersion = RegexedQuestion("Select an OS version {"+ ",".join(map(str,template.getOsVersions())) +"}","[" + ",".join(map(str,template.getOsVersions())) + "]",osVersion).ask()
                        
                    # If there is more than one provisioner available for the template
                    if len(template.getProvisioners()) > 1 :
                        provisioner = Architecture.fromString(RegexedQuestion("Select an Provisioner {"+ ",".join(map(str,template.getProvisioners())) +"}","[" + ",".join(map(str,template.getProvisioners())) + "]",provisioner.name).ask())
                        
                    # If there is more than one provider available for the template
                    if len(template.getProviders()) > 1 :
                        provider = Architecture.fromString(RegexedQuestion("Select an templateProvider {0}".format(",".join(map(str,template.getProviders()))),"[" + ",".join(map(str,template.getProviders())) + "]",provider.name).ask())
                        
                    # Ask for configuration of network interface of the template
                    for f in template.getGuestInterfaces():
                        ipAddr = RegexedQuestion("Enter an IP address for the interface","^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$",f.getIPAddr()).ask()
                        macAddr = RegexedQuestion("Enter a MAC address for the interface","^([a-fA-F0-9]{2}:){5}([a-fA-F0-9]{2})$",f.getMACAddr()).ask()
                        guestInterfaces.append(NetworkInterface(ipAddr,macAddr,f.getHostname()))
                    
                    # Ask for adding a new synced folder
                    while BinaryQuestion("Do you want to add a synced folder ?","N").ask():
                        hostPathQues = PathQuestion("Enter a path to an existing folder on the host",".+",None,True).ask()
                        guestPathQues = PathQuestion("Enter the mount path on the guest directory: ","^/.+",None,False).ask()
                        syncedFolders.append(SyncedFolder(hostPathQues,guestPathQues))
                            
                    COMMANDLINELOGGER.info("The machine named {0} will: ".format(args.name))
                    COMMANDLINELOGGER.info("  Use the architecture {0}".format((arch)))
                    COMMANDLINELOGGER.info("  Use the provisioner {0}".format(str(provisioner)))
                    COMMANDLINELOGGER.info("  Use the provider {0}".format(str(provider)))
                    COMMANDLINELOGGER.info("  Use the host interface {0}".format(hostInterface))
                    i = 0
                    COMMANDLINELOGGER.info("  Have the following network interfaces :")
                    for intf in guestInterfaces:
                        COMMANDLINELOGGER.info("    Name: eth{0}".format(str(i)))
                        COMMANDLINELOGGER.info("    IPAddress: {0}".format(intf.getIPAddr()))
                        COMMANDLINELOGGER.info("    MACAddress: {0}".format(intf.getMACAddr()))
                        if intf.getHostname() != None:
                            COMMANDLINELOGGER.info("    Hostname: {0}".format(intf.getHostname()))
                        COMMANDLINELOGGER.info("")
                        i+=1
                    try:
                        # Try to create the new machine
                        instance = MachineInstance(args.name,template.getName(), arch, osVersion, provider, provisioner, hostInterface, guestInterfaces,syncedFolders)
                        instance.generateFiles()
                    except Exception as e:
                        COMMANDLINELOGGER.error("Unable to create machine: {0}".format(e))
                        res = errno.EINVAL
                else:
                    COMMANDLINELOGGER.error("Unable to create machine: Machine template {0} does not exists".format(args.template))
                    return errno.EINVAL
            else:
                COMMANDLINELOGGER.error("Unable to create machine: Machine named {0} already exists. Change the name of your new machine or delete the existing instance.".format(args.name))
                return errno.EALREADY
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to create machine: {0}.".format(str(e)))
            return errno.EINVAL
        return res
    
    ###
    # Function to destroy a machine
    # Files related to the machine are deleted
    ###
    def destroyMachine(self,args):
        res = 0
        COMMANDLINELOGGER.info("Destroying machine {0}".format(args.name))
        # Getting instances 
        instances = []
        try:
            instanceReg = MachineInstanceRegistry(os.path.join(MACHINATION_USERDIR,'instances'))
            instances = instanceReg.getInstances()        
            # Check if there is actually an instance named after the request of the user
            if args.name in instances.keys():
                # Ask the user if it's ok to delete the machine
                v = BinaryQuestion("Are you sure you want to destroy the machine named {0}. Directory {1}) will be destroyed".format(instances[args.name].getName(),instances[args.name].getPath()),"Y")
                if v == True:
                    instances[args.name].destroy()
                else:
                    COMMANDLINELOGGER.info("Machine not destroyed")
            else:
                COMMANDLINELOGGER.error("Machine {0} does not exist.".format(args.name))
                res = errno.EINVAL
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to destroy machine: {0}".format(str(e)))
            res = errno.EINVAL
        return res
    
    ###
    # Function to start a machine
    # The user must be root to call this function as some stuff related to networking needs to be executed as root
    ###
    def startMachine(self,args):
        res = 0
        COMMANDLINELOGGER.info("Starting machine {0}".format(args.name))
        try:
            # Getting the available instances
            instanceReg = MachineInstanceRegistry(os.path.join(MACHINATION_USERDIR,'instances'))
            instances = instanceReg.getInstances()
            # Check if the requested instance exists
            if args.name in instances.keys():
                instances[args.name].start()
            else:
                COMMANDLINELOGGER.error("Machine {0} does not exist.".format(args.name))
                res = errno.EINVAL
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to start machine {0}: ".format(str(e)))
            res = errno.EINVAL
        return res
    
    ###
    # Function to stop a machine
    # User must be root to call this function juste to be symetric with the start operation
    ###
    def stopMachine(self,args):
        res = 0
        COMMANDLINELOGGER.logger.info("Stopping machine {0}".format(args.name))
        try:
            instanceReg = MachineInstanceRegistry(os.path.join(MACHINATION_USERDIR,'instances'))
            instances = instanceReg.getInstances()
            ## Search for the requested instnce
            if args.name in instances.keys():
                instances[args.name].stop()
            else:
                COMMANDLINELOGGER.error("Machine {0} does not exist.".format(args.name))
                res = errno.EINVAL
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to stop machine {0}: ".format(str(e)))
            res = errno.EINVAL
        return res 
    
    ###
    # Function to connect to the machine in SSH
    ###
    def sshMachine(self,args):
        res = 0
        COMMANDLINELOGGER.info("SSH into machine {0}".format(args.name))
        try:
            ## Search for the requested instance in the registry
            instanceReg = MachineInstanceRegistry(os.path.join(MACHINATION_USERDIR,'instances'))
            instances = instanceReg.getInstances()
            if args.name in instances.keys():
                instances[args.name].ssh()
            else:
                COMMANDLINELOGGER.error("Machine {0} does not exist.".format(args.name))
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to SSH into machine {0}: ".format(str(e)))
            res = errno.EINVAL
        return res 
    
    ###
    # Function to parse the command line arguments
    ### 
    def parseArgs(self,args):
        # Create main parser 
        parser = argparse.ArgumentParser(prog="Machination", description='Machination utility, all your appliances belong to us.')
        rootSubparsers = parser.add_subparsers(help='Root parser')
        
        # Parser for list command
        listParser = rootSubparsers.add_parser('list', help='List templates and instances')
        listSubparsers = listParser.add_subparsers(help='List templates and instances')
        
        templateSubparser = listSubparsers.add_parser('templates', help='List machine templates')
        templateSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List templates")
        templateSubparser.add_argument('dummy',nargs='?', help=argparse.SUPPRESS, action=make_action(self.listTemplates))

        instanceSubparser = listSubparsers.add_parser('instances', help='List instances')
        instanceSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List instances")
        instanceSubparser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.listInstances))
        
        # Parser for create command    
        createParser = rootSubparsers.add_parser('create', help='Create the given machine in the path')
        createParser.add_argument('template', help='Name of the template to create')
        createParser.add_argument('name', help='Name of the machine to create')
        createParser.add_argument('dummy',nargs='?', help=argparse.SUPPRESS,action=make_action(self.createMachine))
        
        # Parser for destroy command
        destroyParser = rootSubparsers.add_parser('destroy', help='Destroy the given machine in the path')
        destroyParser.add_argument('name', help='Name of the machine to destroy')
        destroyParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.destroyMachine))
        
        # Parser for start command
        startParser = rootSubparsers.add_parser('start', help='Start the given machine')
        startParser.add_argument('name', help='Name of the machine to start')
        startParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.startMachine))
        
        # Parser for stop command
        stopParser = rootSubparsers.add_parser('stop', help='Stop the given machine')
        stopParser.add_argument('name', help='Name of the machine to stop')
        stopParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.stopMachine))
        
        # Parser for ssh command
        sshParser = rootSubparsers.add_parser('ssh', help='SSH to the given machine')
        sshParser.add_argument('name', help='Name of the machine to ssh in')
        sshParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.sshMachine))
        
        # Parse the command
        parser.parse_args()
        