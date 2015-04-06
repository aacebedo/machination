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
import re

import machination.helpers
from machination.core import MachineInstance, NetworkInterface
from machination.core import SyncedFolder

from machination.loggers import COMMANDLINELOGGER
from machination.constants import MACHINATION_INSTALLDIR
from machination.constants import MACHINATION_USERTEMPLATESDIR
from machination.constants import MACHINATION_USERINSTANCESDIR
from machination.constants import MACHINATION_DEFAULTTEMPLATESDIR

from machination.registries import MachineTemplateRegistry
from machination.registries import MachineInstanceRegistry

from machination.questions import RegexedQuestion
from machination.questions import BinaryQuestion
from machination.questions import PathQuestion

from machination.enums import Architecture
from machination.enums import Provider
from machination.enums import Provisioner

from machination.exceptions import InvalidCmdLineArgument
from machination.exceptions import InvalidHardwareSupport

from machination.helpers import getAllNetInterfaces

# ##
# Function called by the argument parsing objects
# ##
def make_action(functionToCall):
    class customAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            setattr(args, self.dest, values)
            functionToCall(args)
    return customAction

# ##
# Class used to handle the arguments passed by the command line
# ##
class CmdLine:
    # ##
    # Function used to list available templates
    # Templates are searched in the install directory of machination but also in the user workdir (~/.machination)
    # ##
    def listTemplates(self, args):
        res = 0
        # Create the template registry that will list all available template on the machine
        templateReg = MachineTemplateRegistry([os.path.join(MACHINATION_INSTALLDIR, 'etc','defaults', 'machination', 'templates'), os.path.join(MACHINATION_USERTEMPLATESDIR) ])
        COMMANDLINELOGGER.debug("Listing machine templates")

        try:
            templates = templateReg.getTemplates();
            # Create an array containing a set of informations about the template.
            # This array will be used to display the information to the user
            data = {'name': [], 'version': [], 'path': [], 'provisioners': [], 'providers': [], 'archs': []}
            for f in templates.values():
                data['name'].append(f.getName())
                data['version'].append(f.getVersion())
                data['path'].append(os.path.abspath(f.getPath()))
                data['provisioners'].append(",".join(map(str, f.getProvisioners())))
                data['providers'].append(",".join(map(str, f.getProviders())))
                data['archs'].append(",".join(map(str, f.getArchs())))

            # Each column width will be computed as the max length of its items
            name_col_width = 0
            version_col_width = 0
            path_col_width = 0
            provisioner_col_width = 0
            providers_col_width = 0
            archs_col_width = 0

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
            if len(data['name']) != 0:
                # Display the array titles
                COMMANDLINELOGGER.info("Name".ljust(name_col_width) + "Version".ljust(version_col_width) + "Path".ljust(path_col_width) + "Provisioners".ljust(provisioner_col_width) + "Providers".ljust(providers_col_width) + "Architectures".ljust(archs_col_width))
                for row in range(0, len(data['name'])):
                    COMMANDLINELOGGER.info(data['name'][row].ljust(name_col_width) + data['version'][row].ljust(version_col_width) + data['path'][row].ljust(path_col_width) + data['provisioners'][row].ljust(provisioner_col_width) + data['providers'][row].ljust(providers_col_width) + data['archs'][row].ljust(archs_col_width))
            else:
                COMMANDLINELOGGER.info("No templates available")
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to list templates: {0}".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to list the instances
    # The instances are searched in the user workdir (~/.machination)
    # ##
    def listInstances(self, args):
        res = 0
        COMMANDLINELOGGER.debug("Listing machine instances")
        # Populating the registry of instances
        instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])

        try:
            instances = instanceReg.getInstances()
            # Create an array to display the available templates
            data = {'name': [], 'path': []}
            for i in instances.values():
                data['name'].append(i.getName())
                data['path'].append(i.getPath())

            # Display the array of templates
            # Check if there is an item in the resulting array using the length of the column name
            if len(data['name']) != 0:
                name_col_width = max(len(word) for word in data['name']) + len("Name") + 2
                path_col_width = max(len(word) for word in data['path']) + len("Path") + 2

                COMMANDLINELOGGER.info("Name".ljust(name_col_width) + "Path".ljust(path_col_width))
                for row in range(0, len(data['name'])):
                    COMMANDLINELOGGER.info(data['name'][row].ljust(name_col_width) + data['path'][row].ljust(name_col_width))
            else:
                COMMANDLINELOGGER.info("No instances available")
        except Exception as e:
            print traceback.format_exc()
            COMMANDLINELOGGER.error("Unable to list instances: {0}".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to create a new machine
    # ##
    def createMachine(self, args):
        res = 0
        COMMANDLINELOGGER.info("Creating a new machine instance named '{0}' using template '{1}'".format(args.name, args.template))
        # Creating the template and instances registries
        templateReg = MachineTemplateRegistry([MACHINATION_DEFAULTTEMPLATESDIR,MACHINATION_USERTEMPLATESDIR])
        instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])

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
                    hostInterface = None
                    networkInterfaces = getAllNetInterfaces();
                    if len(networkInterfaces) == 0:
                      raise InvalidHardwareSupport("Your machine does not have any network interface. Machine instances cannot be executed")
                    # Ask for the host interface to use
                    if args.hostinterface != None:
                      hostInterface = args.hostinterface
                      if hostInterface not in networkInterfaces:
                        raise InvalidCmdLineArgument("hostinterface",args.hostinterface)
                    else:
                      hostInterface = RegexedQuestion("Enter the host interface [{0}]".format(",".join(map(str, networkInterfaces))),
                                                       "Host interfaces must be from {0}".format(",".join(map(str, networkInterfaces))),
                                                       COMMANDLINELOGGER,
                                                       "^{0}$".format("\\b|\\b".join(map(str, networkInterfaces))), networkInterfaces[0]).ask()

                    # If there is more than one architecture available for the template
                    # Ask the user to choose
                    if len(template.getArchs()) > 1 :
                        if args.arch != None:
                            try:
                                arch = Architecture.fromString(args.arch)
                            except:
                                raise InvalidCmdLineArgument("architecture",args.arch)
                            if arch not in template.getArchs():
                                raise InvalidCmdLineArgument("architecture",args.arch)
                        else:
                            arch = Architecture.fromString(RegexedQuestion("Select an architecture [{0}]".fomat(",".join(map(str, template.getArchs()))),
                                                                           "Architecture must be from {0}".format(",".join(map(str, template.getArchs()))),
                                                                           COMMANDLINELOGGER,
                                                                           "^[{0}]$".format("\\b|\\b".join(map(str, template.getArchs()))), arch.name).ask())

                    # If there is more than one OS version available for the template
                    # Ask the user to choose
                    if len(template.getOsVersions()) > 1 :
                        if args.osversion != None:
                            osVersion = args.osversion
                        else:
                            osVersion = RegexedQuestion("Select an OS version [{0}]".format(",".join(map(str, template.getOsVersions()))),
                                                        "OS version must be from {0}".format(",".join(map(str, template.getOsVersions()))),
                                                        COMMANDLINELOGGER,
                                                        "[{0}]".format("\\b|\\b".join(map(str, template.getOsVersions()))), osVersion).ask()

                    # If there is more than one provisioner available for the template
                    if len(template.getProvisioners()) > 1 :
                        if args.provisioner != None:
                            try:
                                provisioner = Provisioner.fromString(args.provisioner)
                            except:
                                raise InvalidCmdLineArgument("provisioner",args.provisioner)
                            if provisioner not in template.getProvisioners():
                                raise InvalidCmdLineArgument("provisioner",args.provisioner)
                        else:
                            provisioner = Provisioner.fromString(RegexedQuestion("Select an Provisioner [{0}]".format(",".join(map(str, template.getProvisioners()))),
                                                                                 "Provisioner must be from {0}".format(",".join(map(str, template.getProvisioners()))),
                                                                                 COMMANDLINELOGGER,
                                                                                 "[{0}]".format("\\b|\\b".join(map(str, template.getProvisioners()))),
                                                                                  provisioner.name).ask())

                    # If there is more than one provider available for the template
                    if len(template.getProviders()) > 1 :
                        if args.provider != None:
                            try:
                                provider = Provider.fromString(args.provider)
                            except:
                                raise InvalidCmdLineArgument("provider",args.provider)
                            if provider not in template.getProviders():
                                raise InvalidCmdLineArgument("provider",args.provider)
                        else:
                            provider = Provider.fromString(RegexedQuestion("Select a Provider {0}".format(",".join(map(str, template.getProviders()))),
                                                                           "Provider must be from {0}".format(",".join(map(str, template.getProviders()))),
                                                                           COMMANDLINELOGGER,
                                                                           "[{0}]".format("\\b|\\b".join(map(str, template.getProviders()))), provider.name).ask())

                    # Ask for configuration of network interface of the template
                    itfCounter = 0
                    if args.guestinterface!= None:
                      if type(args.guestinterface) is list and len(args.guestinterface)>=len(template.getGuestInterfaces()):
                        for i in template.getGuestInterfaces():
                            m = re.search("^(.*)\|(.*)\|(.*)",args.guestinterface[itfCounter])
                            if m != None:
                                hostname = m.group(1)
                                ipAddr = m.group(2)
                                macAddr = m.group(3)
                                guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
                                itfCounter+=1
                            else:
                                raise InvalidCmdLineArgument("guestinterface",args.guestinterface[itfCounter])

                        for i in range(itfCounter, len(args.guestinterface)):
                          m = re.search("^(.*)\|(.*)\|(.*)",args.guestinterface[itfCounter])
                          if m != None:
                            hostname = m.group(1)
                            ipAddr = m.group(2)
                            macAddr = m.group(3)
                            guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
                          else:
                            raise InvalidCmdLineArgument("guestinterface")
                      else:
                          raise InvalidCmdLineArgument("Not enough interfaces for given template")
                    else:
                      hostnameRegex = "([0-9a-zA-Z]*)"
                      ipAddrRegex = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp"
                      macAddrRegex = "([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})"
                      counter = 0
                      for i in template.getGuestInterfaces():
                        hostname = RegexedQuestion("Enter an Hostname for the interface eth{0}".format(counter),
                                                   "Hostname must be a string",
                                                    COMMANDLINELOGGER,
                                                    "^{0}$".format(hostnameRegex), i.getHostname()).ask()
                        ipAddr = RegexedQuestion("Enter an IP address for the interface",
                                                    "IPAddress must be of form XXX.XXX.XXX.XXX",
                                                    COMMANDLINELOGGER,
                                                    "^{0}$".format(ipAddrRegex),
                                                    i.getIPAddr()).ask()
                        macAddr = RegexedQuestion("Enter a MAC address for the interface",
                                                  "MAC address must be of form XX:XX:XX:XX:XX",
                                                    COMMANDLINELOGGER,
                                                  "^{0}$".format(macAddrRegex), i.getMACAddr()).ask()
                        guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
                        counter+=1

                      # Ask for additional network interfaces
                      if args.quiet == False:
                        while BinaryQuestion("Do you want to add an additional network interface?","Enter a Y or a N",COMMANDLINELOGGER, "N").ask():
                          hostname = RegexedQuestion("Enter an Hostname for the interface",
                                                    "Hostname must be a string",
                                                    COMMANDLINELOGGER,
                                                    "^{0}$".format(hostnameRegex),
                                                     "Enter a Y or a N",COMMANDLINELOGGER, "").ask()
                          ipAddr = RegexedQuestion("Enter an IP address for the interface",
                                                   "IPAddress must be of form XXX.XXX.XXX.XXX",
                                                    COMMANDLINELOGGER,
                                                   "^{0}$".format(ipAddrRegex),"Enter a Y or a N",COMMANDLINELOGGER, "").ask()
                          macAddr = RegexedQuestion("Enter a MAC address for the interface",
                                                    "MAC address must be of form XX:XX:XX:XX:XX",
                                                    COMMANDLINELOGGER,
                                                     "^{0}$".format(macAddrRegex),"Enter a Y or a N",COMMANDLINELOGGER, machination.helpers.randomMAC()).ask()
                          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))

                    if args.quiet == False:
                      # Ask for adding a new synced folder
                      while BinaryQuestion("Do you want to add a synced folder ?",
                                           "Enter a Y or a N",COMMANDLINELOGGER, "N").ask():
                          hostPathQues = PathQuestion("Enter a path to an existing folder on the host",
                                                      "Entered path is invalid, Please enter a valid path",
                                                      COMMANDLINELOGGER,
                                                      ".+", None, True).ask()
                          guestPathQues = PathQuestion("Enter the mount path on the guest directory: ",
                                                       "Entered path is invalid, Please enter a valid path",
                                                       COMMANDLINELOGGER,
                                                       "^/.+", None, False).ask()
                          syncedFolders.append(SyncedFolder(hostPathQues, guestPathQues))

                    if args.sharedfolder != None:
                      for s in args.sharedfolder:
                        regex = "^(.*)\|(.*)$"
                        m = re.search(regex,s)
                        if m != None:
                          syncedFolders.append(SyncedFolder(m.group(1), m.group(2)))
                        else:
                          raise InvalidCmdLineArgument("sharedfolder",s)
                    try:
                        # Try to create the new machine
                        instance = MachineInstance(args.name, template, arch, osVersion, provider, provisioner, hostInterface, guestInterfaces, syncedFolders)
                        instance.generateFiles()
                        COMMANDLINELOGGER.info("Summary of the created machine:")
                        instances = instanceReg.getInstances()
                        COMMANDLINELOGGER.info(instances[args.name].getInfos())
                    except Exception as e:
                        COMMANDLINELOGGER.error("Unable to create machine instance {0}.".format(e))
                        res = errno.EINVAL
                else:
                    COMMANDLINELOGGER.error("Unable to create machine: Machine template '{0}' does not exists".format(args.template))
                    return errno.EINVAL
            else:
                COMMANDLINELOGGER.error("Unable to create machine: Machine instance named '{0}' already exists. Change the name of your new machine instance or delete the existing instance.".format(args.name))
                return errno.EALREADY
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to create machine instance {0}.".format(str(e)))
            return errno.EINVAL
        return res

    # ##
    # Function to destroy a machine
    # Files related to the machine are deleted
    # ##
    def destroyMachine(self, args):
        res = 0
        # Getting instances
        instances = []
        try:
            instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])
            instances = instanceReg.getInstances()
            # Check if there is actually an instance named after the request of the user
            if args.name in instances.keys():
                # Ask the user if it's ok to delete the machine
                v = args.force
                if v == False:
                  v = BinaryQuestion("Are you sure you want to destroy the machine named {0}. Directory {1}) will be destroyed".format(instances[args.name].getName(),
                                                                                                                                       instances[args.name].getPath()),
                                                                                                                                       "Enter a Y or a N",COMMANDLINELOGGER, "Y").ask()
                if v == True:
                    COMMANDLINELOGGER.info("Destroying machine instance '{0}'...".format(args.name))
                    instances[args.name].destroy()
                    COMMANDLINELOGGER.info("Machine instance successfully destroyed")
                else:
                    COMMANDLINELOGGER.info("Machine not destroyed")
            else:
                COMMANDLINELOGGER.error("Machine instance '{0}' does not exist.".format(args.name))
                res = errno.EINVAL
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to destroy machine '{0}'".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to start a machine
    # The user must be root to call this function as some stuff related to networking needs to be executed as root
    # ##
    def startMachineInstance(self, args):
        res = 0
        COMMANDLINELOGGER.info("Starting machine {0}".format(args.name))
        try:
            # Getting the available instances
            instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])
            instances = instanceReg.getInstances()
            # Check if the requested instance exists
            if args.name in instances.keys():
                instances[args.name].start()
            else:
                COMMANDLINELOGGER.error("Machine instance '{0}' does not exist.".format(args.name))
                res = errno.EINVAL
            COMMANDLINELOGGER.info("Machine instance '{0}' successfully started.".format(args.name))
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to start machine instance '{0}'.".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to stop a machine
    # User must be root to call this function juste to be symetric with the start operation
    # ##
    def stopMachineInstance(self, args):
        res = 0
        COMMANDLINELOGGER.info("Stopping machine {0}".format(args.name))
        try:
            instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])
            instances = instanceReg.getInstances()
            # # Search for the requested instnce
            if args.name in instances.keys():
                instances[args.name].stop()
            else:
                COMMANDLINELOGGER.error("Machine instance '{0}' does not exist.".format(args.name))
                res = errno.EINVAL
            COMMANDLINELOGGER.info("Machine instance '{0}' successfully stopped.".format(args.name))
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to stop machine instance '{0}'.".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to restart a machine
    # User must be root to call this function juste to be symetric with the start and stop operations
    # ##
    def restartMachineInstance(self, args):
        self.stopMachineInstance(args)
        return self.startMachineInstance(args)

    # ##
    # Function to get infos from a machine instance
    # ##
    def getMachineInstanceInfos(self, args):
        res = 0
        COMMANDLINELOGGER.info("Retrieving information for machine instance '{0}'".format(args.name))
        try:
            instanceReg = MachineInstanceRegistry([MACHINATION_USERINSTANCESDIR])
            instances = instanceReg.getInstances()
            # # Search for the requested instnce
            if args.name in instances.keys():
                COMMANDLINELOGGER.info(instances[args.name].getInfos())
            else:
                COMMANDLINELOGGER.error("Machine instance '{0}' does not exist.".format(args.name))
                res = errno.EINVAL
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to get informations for machine instance '{0}': '{1}'.".format(args.name,str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to connect to the machine in SSH
    # ##
    def sshMachine(self, args):
        res = 0
        COMMANDLINELOGGER.info("SSH into machine {0}".format(args.name))
        try:
            # # Search for the requested instance in the registry
            instanceReg = MachineInstanceRegistry([os.path.join(MACHINATION_USERINSTANCESDIR)])
            instances = instanceReg.getInstances()
            if args.name in instances.keys():
                instances[args.name].ssh()
            else:
                COMMANDLINELOGGER.error("Machine instance '{0}' does not exist.".format(args.name))
        except Exception as e:
            COMMANDLINELOGGER.error("Unable to SSH into machine instance '{0}': ".format(str(e)))
            res = errno.EINVAL
        return res

    # ##
    # Function to parse the command line arguments
    # ##
    def parseArgs(self, args):
        # Create main parser
        parser = argparse.ArgumentParser(prog="Machination", description='Machination utility, all your appliances belong to us.')
        rootSubparsers = parser.add_subparsers(help='Root parser')

        # Parser for list command
        listParser = rootSubparsers.add_parser('list', help='List templates and instances')
        listSubparsers = listParser.add_subparsers(help='List templates and instances')

        templateSubparser = listSubparsers.add_parser('templates', help='List machine templates')
        templateSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List templates")
        templateSubparser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.listTemplates))

        instanceSubparser = listSubparsers.add_parser('instances', help='List instances')
        instanceSubparser.add_argument('provisioner', choices=['ansible'], nargs='*', default='ansible', help="List instances")
        instanceSubparser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.listInstances))

        # Parser for create command
        createParser = rootSubparsers.add_parser('create', help='Create the given machine in the path')
        createParser.add_argument('template', help='Name of the template to create', type=str)
        createParser.add_argument('name', help='Name of the machine to create', type=str)
        createParser.add_argument('--arch', help='Architecture of new the machine', type=str)
        createParser.add_argument('--provider', help='Provider to use for the new machine', type=str)
        createParser.add_argument('--provisioner', help='Provisioner to use for the new machine', type=str)
        createParser.add_argument('--osversion', help='OS Version of the new machine', type=str)
        createParser.add_argument('--hostinterface', help='Network interface of the host for the new machine',type=str)
        createParser.add_argument('--guestinterface', help='Network interface to add to the new machine <hostname|ip_addr|mac_addr>', action='append', type=str)
        createParser.add_argument('--sharedfolder', help='Shared folder to ad to the new machine <host_folder|guest_folder>', action='append', type=str)
        createParser.add_argument('--quiet', help='Do not request for interactive configuration of optional elements (interfaces,sharedfolders) of the instance', action='store_true')
        createParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.createMachine))

        # Parser for destroy command
        destroyParser = rootSubparsers.add_parser('destroy', help='Destroy the given machine in the path')
        destroyParser.add_argument('name', help='Name of the machine to destroy')
        destroyParser.add_argument('--force', help='Do not ask for confirmation', action='store_true')
        destroyParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.destroyMachine))

        # Parser for start command
        startParser = rootSubparsers.add_parser('start', help='Start the given machine instance')
        startParser.add_argument('name', help='Name of the machine to start')
        startParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.startMachineInstance))

        # Parser for stop command
        stopParser = rootSubparsers.add_parser('stop', help='Stop the given machine instance')
        stopParser.add_argument('name', help='Name of the machine to stop')
        stopParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.stopMachineInstance))

        # Parser for restart command
        restartParser = rootSubparsers.add_parser('restart', help='Restart the given machine instance')
        restartParser.add_argument('name', help='Name of the machine to restart')
        restartParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.restartMachineInstance))

        # Parser for infos command
        infosParser = rootSubparsers.add_parser('infos', help='Get informations about a machine instance')
        infosParser.add_argument('name', help='Name of the machine instance from which infos shall be retrieved')
        infosParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.getMachineInstanceInfos))

        # Parser for ssh command
        sshParser = rootSubparsers.add_parser('ssh', help='SSH to the given machine')
        sshParser.add_argument('name', help='Name of the machine to ssh in')
        sshParser.add_argument('dummy', nargs='?', help=argparse.SUPPRESS, action=make_action(self.sshMachine))

        # Parse the command
        parser.parse_args()
