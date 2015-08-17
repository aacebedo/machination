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

import argparse, argcomplete
import os
import errno
import traceback

import logging
from distutils.version import StrictVersion
import machination.helpers
from machination.core import MachineInstance, NetworkInterface
from machination.core import SharedFolder

from machination.loggers import COMMANDLINELOGGER, setGlobalLogLevel

from machination.questions import RegexedQuestion
from machination.questions import BinaryQuestion
from machination.questions import PathQuestion

from machination.enums import Architecture
from machination.providers import Provider
from machination.provisioners import Provisioner

from machination.exceptions import InvalidCmdLineArgument
from machination.exceptions import InvalidHardwareSupport

from machination.helpers import getAllNetInterfaces
from machination.globals import MACHINE_INSTANCE_REGISTRY
from machination.globals import MACHINE_TEMPLATE_REGISTRY
from machination.constants import MACHINATION_VERSIONFILE


class MachineInstanceCreationWizard:
  def unpackInterface(self,strCmdLine):
    pack = strCmdLine.split(',')
    if len(pack)==3:
      (ipAddr,macAddr,hostname) = pack
    elif len(pack)==2:
      (ipAddr,macAddr,hostname) = pack + [None]
    else:
        raise InvalidCmdLineArgument("guestinterface", strCmdLine )
    if(macAddr == "auto" or macAddr == None):
        macAddr = machination.helpers.randomMAC()
    print((ipAddr,macAddr,hostname))
    return (ipAddr,macAddr,hostname)
  
  
  def requestGuestInterface(self,networkInterfaces):
    hostnameRegex = "([0-9a-zA-Z]*)"
    ipAddrRegex = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp"
    macAddrRegex = "([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})"
    counter = 0
    hostname = RegexedQuestion("Enter an Hostname for the interface eth{0}".format(counter),
                               "Hostname must be a string",
                                COMMANDLINELOGGER,
                                "^{0}$".format(hostnameRegex), "").ask()
    ipAddr = RegexedQuestion("Enter an IP address for the interface",
                             "IPAddress must be of form XXX.XXX.XXX.XXX",
                             COMMANDLINELOGGER,
                             "^{0}$".format(ipAddrRegex),"dhcp").ask()
    macAddr = RegexedQuestion("Enter a MAC address for the interface",
                              "MAC address must be of form XX:XX:XX:XX:XX",
                              COMMANDLINELOGGER,
                              "^{0}$".format(macAddrRegex), machination.helpers.randomMAC()).ask()
    return (hostname,ipAddr,macAddr)
  
  def requestProvider(self,args,template):
    provider = template.getProviders()[0]
    # If there is more than one provider available for the template
    if len(template.getProviders()) == 1:
      COMMANDLINELOGGER.debug("Template has only one providers. It will be used as the default value")
    else:
      if args.provider != None:
        try:
          provider = Provider.fromString(args.provider)()
        except:
          raise InvalidCmdLineArgument("provider", args.provider)
      else:
        if args.no_interactive == False:
          provider = Provider.fromString(RegexedQuestion("Select a Provider [{0}]".format(",".join(map(str, template.getProviders()))),
                                                         "Provider must be from {0}".format(",".join(map(str, template.getProviders()))),
                                                         COMMANDLINELOGGER,
                                                         "[{0}]".format("\\b|\\b".join(map(str, template.getProviders()))), str(template.getProviders()[0])).ask())()
        else:
          COMMANDLINELOGGER.debug("Missing provider argument")
          raise InvalidCmdLineArgument("provider", args.provider)
    return provider

  def requestProvisionner(self,args,template):
    provisioner = template.getProvisioners()[0]
    # If there is more than one provisioner available for the template
    if len(template.getProvisioners()) == 1:
      COMMANDLINELOGGER.debug("Template has only one provisioner. It will be used as the default value")
    else:
      if args.provisioner != None:
        COMMANDLINELOGGER.debug("A provisioner has been given by the user.")
        try:
          provisioner = Provisioner.fromString(args.provisioner)()
        except:
          COMMANDLINELOGGER.debug("Given provisioner is not supported by machination.")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
        if provisioner not in template.getProvisioners():
          COMMANDLINELOGGER.debug("Given provisioner is not supported by this template.")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
      else:
        if args.no_interactive == False:
          COMMANDLINELOGGER.debug("Request a provisioner to the user.")
          provisioner = Provisioner.fromString(RegexedQuestion("Select an Provisioner [{0}]".format(",".join(map(str, template.getProvisioners()))),
                                                             "Provisioner must be from {0}".format(",".join(map(str, template.getProvisioners()))),
                                                             COMMANDLINELOGGER,
                                                             "[{0}]".format("\\b|\\b".join(map(str, template.getProvisioners()))),
                                                              provisioner.name).ask())()
        else:
          COMMANDLINELOGGER.debug("Missing provisioner argument")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
              
    return provisioner

  def requestOsVersion(self,args,template):
    osVersion = template.getOsVersions()[0]
    # If there is more than one OS version available for the template
    # Ask the user to choose
    if len(template.getOsVersions()) > 1 :
      if args.osversion != None:
        osVersion = args.osversion
        COMMANDLINELOGGER.debug("An os version has been given by the user.")
      else:
        if args.no_interactive == False:
          COMMANDLINELOGGER.debug("Request an os version to the user.")
          osVersion = RegexedQuestion("Select an OS version [{0}]".format(",".join(map(str, template.getOsVersions()))),
                                    "OS version must be from {0}".format(",".join(map(str, template.getOsVersions()))),
                                    COMMANDLINELOGGER,
                                      "[{0}]".format("\\b|\\b".join(map(str, template.getOsVersions()))), osVersion).ask()
        else:
          COMMANDLINELOGGER.debug("Missing os version argument")
          raise InvalidCmdLineArgument("osversion", args.osversion)
    else:
      COMMANDLINELOGGER.debug("Template has only one os version. It will be used as the default value")

    return osVersion
              
  def requestArchitecture(self,args,template):
    arch = template.getArchs()[0]
    # If there is more than one architecture available for the template
    # Ask the user to choose
    if len(template.getArchs()) > 1 :
      if args.arch != None:
        COMMANDLINELOGGER.debug("An architecture has been given in by the user.")
        try:
          arch = Architecture.fromString(self.args.arch)
        except:                        
          COMMANDLINELOGGER.debug("Given architecture is not supported by machination.")
          raise InvalidCmdLineArgument("architecture", self.args.arch)
        if arch not in self.template.getArchs():
          COMMANDLINELOGGER.debug("Given architecture is not supported by the template (shall be one of %s).".format(', '.join(template.getArchs())))
          raise InvalidCmdLineArgument("architecture", self.args.arch)
      else:
        if args.no_interactive == False: 
          COMMANDLINELOGGER.debug("Request an architecture...")
          arch = Architecture.fromString(RegexedQuestion("Select an architecture [{0}]".format(",".join(map(str, template.getArchs()))),
                                                         "Architecture must be from {0}".format(",".join(map(str, template.getArchs()))),
                                                         COMMANDLINELOGGER,
                                                         "^[{0}]$".format("\\b|\\b".join(map(str, template.getArchs()))), arch.name).ask())
        else:
          COMMANDLINELOGGER.debug("Missing architecture argument")
          raise InvalidCmdLineArgument("architecture", args.arch)
    else:
      COMMANDLINELOGGER.debug("Template has only one architecture. It will be used as the default value.")
      
    return arch
      
  def execute(self,args,templates):
    # Check if the requested template exists
    COMMANDLINELOGGER.debug("Instance '{0}' does not exist, proceeding to its creation.".format(args.name))
    args.template = args.template.replace("\\",'')
    
    template = None
    guestInterfaces = []
    sharedFolders = []
    hostInterface = None
    networkInterfaces = getAllNetInterfaces();
    arch = None
    osversion = None
    provisioner = None
    provider = None
      
    if args.template in templates.keys():
      template = templates[args.template]
      guestInterfaces = []
      sharedFolders = []
      hostInterface = None
      networkInterfaces = getAllNetInterfaces();
      
      hostInterface = None
      if len(networkInterfaces) == 0:
        COMMANDLINELOGGER.debug("No ethernet interfaces has been found on the host.")
        raise InvalidHardwareSupport("Your host does not have any network interface. Machines cannot be executed")
      else:
        COMMANDLINELOGGER.debug("{0} interfaces has been found on the host: {1}.".format(len(networkInterfaces),', '.join(networkInterfaces)))
        hostInterface = RegexedQuestion("Enter the host interface on which the guest interfaces will be bridged [{0}]".format(",".join(map(str, networkInterfaces))),
                                    "Host interfaces must be from {0}".format(",".join(map(str, networkInterfaces))),
                                    COMMANDLINELOGGER,
                                    "^{0}$".format("\\b|\\b".join(map(str, networkInterfaces))), networkInterfaces[0]).ask()
    
      arch = self.requestArchitecture(args,template)
      osversion = self.requestOsVersion(args,template)
      provisioner = self.requestProvisionner(args,template)
      provider = self.requestProvider(args,template) 
        
      # Ask for configuration of network interface of the template
      itfCounter = 0
      if args.guestinterface != None:
        for i in range(0,template.getGuestInterfaces()):
          (ipAddr,macAddr,hostname) = self.unpackInterface(args.guestinterface[itfCounter] )
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
        for i in range(itfCounter, len(args.guestinterface)):
          (ipAddr,macAddr,hostname) = self.unpackInterface(args.guestinterface[itfCounter] )
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr,hostname))
          itfCounter += 1
      else:
        for i in range(0,template.getGuestInterfaces()):
          (ipAddr,macAddr,hostname) = self.requestInterface(networkInterfaces)
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))

      # Ask for additional network interfaces
      if args.no_interactive == False:
        for i in range(itfCounter,template.getGuestInterfaces()):
          (ipAddr,macAddr,hostname) = self.requestInterface(networkInterfaces)
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
      else:
        if(len(args.guestinterface) < template.getGuestInterfaces()):
          COMMANDLINELOGGER.error("Not enough guestinterfaces given to fill requirement of template")
          raise InvalidCmdLineArgument("guestinterface", args.guestinterface)

      if args.no_interactive == False:
        # Ask for adding a new shared folder
        while BinaryQuestion("Do you want to add a shared folder ?",
                           "Enter a Y or a N", COMMANDLINELOGGER, "N").ask():
          hostPathQues = PathQuestion("Enter a path to an existing folder on the host",
                                    "Entered path is invalid, Please enter a valid path",
                                    COMMANDLINELOGGER,
                                    ".+", None, True).ask()
          guestPathQues = PathQuestion("Enter the mount path on the guest directory: ",
                                     "Entered path is invalid, Please enter a valid path",
                                     COMMANDLINELOGGER,
                                     "^/.+", None, False).ask()
          sharedFolders.append(SharedFolder(hostPathQues, guestPathQues))

        if args.sharedfolder != None:
          for s in args.sharedfolder:
            sharedFolders.append(SharedFolder(s[0], s[1]))
        
    else:
      COMMANDLINELOGGER.error("Unable to create machine: MachineInstance template '{0}:{1}' does not exists".format(args.template,args.templateversion))

      
    return (template, arch, osversion, provider, provisioner, guestInterfaces, hostInterface, sharedFolders) 
# ##
# Class used to handle the arguments passed by the command line
# ##
class CmdLine:
    # ##
    # Function used to list available templates
    # Templates are searched in the install directory of machination but also in the user workdir (~/.machination)
    # ##
    def listElements(self, args):
      listFunctions = {
       "templates":self.listMachineTemplates,
       "instances":self.listMachineInstances,
      }
      
      if(args.type == None or args.type not in listFunctions.keys()):
        self.listMachineTemplates(args)
        self.listMachineInstances(args)
      else:
        listFunctions[args.type](args)
      
    # ##
    # Function used to list available templates
    # Templates are searched in the install directory of machination but also in the user workdir (~/.machination)
    # ##
    def listMachineTemplates(self, args):
      res = 0
      # Create the template registry that will list all available template on the machine
      COMMANDLINELOGGER.info("Machine templates:")
      COMMANDLINELOGGER.info("-------------------")
      
      try:
        templates = MACHINE_TEMPLATE_REGISTRY.getTemplates();
        COMMANDLINELOGGER.debug("Templates loaded.")
        # Create an array containing a set of informations about the template.
        # This array will be used to display the information to the user
        data = {'name': [], 'version': [], 'path': [], 'provisioners': [], 'providers': [], 'archs': [],'comments': []}
        for f in templates.values():
          data['name'].append(f.getName())
          data['path'].append(os.path.abspath(f.getPath()))
          data['provisioners'].append(",".join(map(str, f.getProvisioners())))
          data['providers'].append(",".join(map(str, f.getProviders())))
          data['archs'].append(",".join(map(str, f.getArchs())))
          data['comments'].append(f.getComments())

        # Each column width will be computed as the max length of its items
        name_col_width = 0
        path_col_width = 0
        provisioner_col_width = 0
        providers_col_width = 0
        archs_col_width = 0
        comments_col_width = 0

        # Getting the max for each column
        if len(data['name']) != 0:
          name_col_width = max(len(word) for word in data['name']) + len("Name") + 2
        if len(data['path']) != 0:
          path_col_width = max(len(word) for word in data['path']) + len("Path") + 2
        if len(data['provisioners']) != 0:
          provisioner_col_width = max(len(word) for word in data['provisioners']) + len("Provisioners") + 2
        if len(data['providers']) != 0:
          providers_col_width = max(len(word) for word in data['providers']) + len("Providers") + 2
        if len(data['archs']) != 0:
          archs_col_width = max(len(word) for word in data['archs']) + len("Architectures") + 2
        if len(data['comments']) != 0:
          comments_col_width = max(len(word) for word in data['comments']) + len("Comments") + 2
        
        
        # Display the array
        # Checking number of items in the column name to know if there is something to display or not
        if len(data['name']) != 0:
          # Display the array titles
          COMMANDLINELOGGER.info("Name".ljust(name_col_width) + 
                                  "Path".ljust(path_col_width) + 
                                  "Provisioners".ljust(provisioner_col_width) + 
                                  "Providers".ljust(providers_col_width) + 
                                  "Architectures".ljust(archs_col_width) + 
                                  "Comments".ljust(comments_col_width))
                                  
          for row in range(0, len(data['name'])):
              COMMANDLINELOGGER.info(data['name'][row].ljust(name_col_width) +  
                                     data['path'][row].ljust(path_col_width) + 
                                     data['provisioners'][row].ljust(provisioner_col_width) +
                                     data['providers'][row].ljust(providers_col_width) + 
                                     data['archs'][row].ljust(archs_col_width) +
                                     data['comments'][row].ljust(comments_col_width))
        else:
          COMMANDLINELOGGER.info("No templates available")
      except Exception as e:
        COMMANDLINELOGGER.error("Unable to list templates: {0}".format(str(e)))
        if (not args.verbose):
          COMMANDLINELOGGER.info("Run with --verbose flag for more details")
        COMMANDLINELOGGER.debug(traceback.format_exc())
        res = errno.EINVAL
      except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
          
      COMMANDLINELOGGER.info("")
      
      return res

    # ##
    # Function to list the instances
    # The instances are searched in the user workdir (~/.machination)
    # ##
    def listMachineInstances(self, args):
        COMMANDLINELOGGER.info("Machine instances:")
        COMMANDLINELOGGER.info("-------------------")
        res = 0
        try:
          instances = MACHINE_INSTANCE_REGISTRY.getInstances()
          COMMANDLINELOGGER.debug("Instances loaded.")

          # Create an array to display the available templates
          data = {'name': [], 'path': [], 'started': []}
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
          COMMANDLINELOGGER.error("Unable to list instances: {0}".format(str(e)))
          if (not args.verbose):
            COMMANDLINELOGGER.info("Run with --verbose flag for more details")
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
        COMMANDLINELOGGER.info("")
        return res
      
    # ##
    # Function to create a new machine
    # ##
    def createMachineInstance(self, args):
      res = 0
      COMMANDLINELOGGER.info("Creating a new machine instance named '{0}' using template '{1}'".format(args.name, args.template))
      # Creating the template and instances registries

      try:
        templates = []
        instances = []
        # Get templates
        templates = MACHINE_TEMPLATE_REGISTRY.getTemplates()
        COMMANDLINELOGGER.debug("Templates loaded.")
        
        # Get instances
        instances = MACHINE_INSTANCE_REGISTRY.getInstances()
        COMMANDLINELOGGER.debug("Instances loaded.")
        # Check if the instance is already in the registry
        if args.force :
          if args.name in instances.keys():
            COMMANDLINELOGGER.error("Machine instance named '{0}' already exists but creation was forced so firstly machination will delete it.".format(args.name))
            instances[args.name].destroy()
      
        if args.force == False and args.name in instances.keys():
            COMMANDLINELOGGER.error("Unable to create machine: MachineInstance named '{0}' already exists. Change the name of your new machine or delete the existing one.".format(args.name))
            res = errno.EALREADY
        else:
          (template, arch, osversion, provider, provisioner, guestInterfaces, hostInterface, sharedFolders) =  MachineInstanceCreationWizard().execute(args,templates)
          # Try to create the new machine
          instance = MachineInstance(args.name, template, arch, osversion, provider, provisioner, guestInterfaces, hostInterface, sharedFolders)
          instance.create()
          COMMANDLINELOGGER.info("MachineInstance successfully created:")
          instances = MACHINE_INSTANCE_REGISTRY.getInstances()
          COMMANDLINELOGGER.info(instances[args.name].getInfos())

      
      except (KeyboardInterrupt, SystemExit):
        COMMANDLINELOGGER.debug(traceback.format_exc())
        res = errno.EINVAL          
      except Exception as e:
        COMMANDLINELOGGER.error("Unable to create machine instance '{0}': {1}.".format(args.name,str(e)))
        if (not args.verbose):
          COMMANDLINELOGGER.info("Run with --verbose flag for more details")
        COMMANDLINELOGGER.debug(traceback.format_exc())
        res = errno.EINVAL
        
      return res

    # ##
    # Function to destroy a machine
    # Files related to the machine are deleted
    # ##
    def destroyMachineInstance(self, args):
      res = 0
      
      for name in args.names:
        try:
          # Getting instances
          instances = MACHINE_INSTANCE_REGISTRY.getInstances()
          # Check if there is actually an instance named after the request of the user
          if name in instances.keys():
            # Ask the user if it's ok to delete the machine
            v = args.force
            if v == False:
              v = BinaryQuestion("Are you sure you want to destroy the machine named {0}. Directory {1}) will be destroyed".format(instances[name].getName(),
                                                                                                                                   instances[name].getPath()),
                                                                                                                                   "Enter a Y or a N", COMMANDLINELOGGER, "Y").ask()
            if v == True:
              COMMANDLINELOGGER.info("Destroying machine instance '{0}'...".format(name))
              instances[name].destroy()
              COMMANDLINELOGGER.info("MachineInstance instance successfully destroyed")
            else:
              COMMANDLINELOGGER.info("MachineInstance not destroyed")
          else:
            COMMANDLINELOGGER.error("MachineInstance instance '{0}' does not exist.".format(name))
            res = errno.EINVAL
        except Exception as e:
          COMMANDLINELOGGER.error("Unable to destroy machine '{0}': {1}".format(name,str(e)))
          if (not args.verbose):
            COMMANDLINELOGGER.info("Run with --verbose flag for more details")
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
      return res

    # ##
    # Function to start a machine
    # The user must be root to call this function as some stuff related to networking needs to be executed as root
    # ##
    def startMachineInstance(self, args):
      res = 0
      for name in args.names:
        COMMANDLINELOGGER.info("Starting machine {0}".format(name))
        try:
          # Getting the available instances
          instances = MACHINE_INSTANCE_REGISTRY.getInstances()
          # Check if the requested instance exists
          if name in instances.keys():
            instances[name].start()
          else:
            COMMANDLINELOGGER.error("MachineInstance instance '{0}' does not exist.".format(name))
            res = errno.EINVAL
          COMMANDLINELOGGER.info("MachineInstance instance '{0}' successfully started.".format(name))
        except Exception as e:
          COMMANDLINELOGGER.error("Unable to start machine instance '{0}': {1}.".format(name,str(e)))
          COMMANDLINELOGGER.debug(traceback.format_exc())
          if (not args.verbose):
            COMMANDLINELOGGER.info("Run with --verbose flag for more details")
          res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
      return res

    # ##
    # Function to stop a machine
    # User must be root to call this function juste to be symetric with the start operation
    # ##
    def stopMachineInstance(self, args):
      res = 0
      for name in args.names:
        print(name)
        COMMANDLINELOGGER.info("Stopping machine {0}".format(name))
        try:
          instances = MACHINE_INSTANCE_REGISTRY.getInstances()
          # # Search for the requested instnce
          if name in instances.keys():
            instances[name].stop()
          else:
            COMMANDLINELOGGER.error("MachineInstance instance '{0}' does not exist.".format(name))
          COMMANDLINELOGGER.info("MachineInstance instance '{0}' successfully stopped.".format(name))
        except Exception as e:
          COMMANDLINELOGGER.error("Unable to stop machine instance '{0}': {1}.".format(name,str(e)))
          if (not args.verbose):
            COMMANDLINELOGGER.info("Run with --verbose flag for more details")
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
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
      toDisplay =  []
      if(args.names):
        toDisplay.append(args.names)
      
      instances = MACHINE_INSTANCE_REGISTRY.getInstances()
      
      if(len(toDisplay) == 0):
        toDisplay = instances.keys()
      
      for name in toDisplay:
        try:

          # # Search for the requested instnce
          if name in instances.keys():
            COMMANDLINELOGGER.info(instances[name].getInfos())
          else:
            COMMANDLINELOGGER.error("MachineInstance instance '{0}' does not exist.".format(name))
            res = errno.EINVAL
        except Exception as e:
          COMMANDLINELOGGER.error("Unable to get informations for machine instance '{0}': '{1}'.".format(name, str(e)))
          if (not args.verbose):
            COMMANDLINELOGGER.info("Run with --verbose flag for more details")
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
          COMMANDLINELOGGER.debug(traceback.format_exc())
          res = errno.EINVAL
      return res

    # ##
    # Function to connect to the machine in SSH
    # ##
    def sshIntoMachineInstance(self, args):
      res = 0
      COMMANDLINELOGGER.info("SSH into machine {0}".format(args.name))
      try:
        # # Search for the requested instance in the registry
        instances = MACHINE_INSTANCE_REGISTRY.getInstances()
        if args.name in instances.keys():
          if not instances[args.name].isStarted() :
            COMMANDLINELOGGER.error("MachineInstance instance '{0}' is not started, starting it before connecting to it.".format(args.name))
            instances[args.name].start()

          instances[args.name].ssh(args.command)
        else:
          COMMANDLINELOGGER.error("MachineInstance instance '{0}' does not exist.".format(args.name))
      except Exception as e:
        COMMANDLINELOGGER.error("Unable to SSH into machine instance '{0}': ".format(str(e)))
        if (not args.verbose):
          COMMANDLINELOGGER.info("Run with --verbose flag for more details")
        COMMANDLINELOGGER.debug(traceback.format_exc())
        res = errno.EINVAL
      except (KeyboardInterrupt, SystemExit):
        COMMANDLINELOGGER.debug(traceback.format_exc())
      return res
  
    def displayVersion(self,args):
      version = "Unknown version"
      
      try:
        version_file = open(MACHINATION_VERSIONFILE,'r')
        version = StrictVersion(version_file.read())
      except:
        pass
      COMMANDLINELOGGER.info("Machination {0}".format(str(version)))
      
    # ##
    # Function to parse the command line arguments
    # ##
    def parseArgs(self, args):      
      templates = MACHINE_TEMPLATE_REGISTRY.getTemplates()
      COMMANDLINELOGGER.debug("Templates loaded.")
          
      # Get instances
      instances = MACHINE_INSTANCE_REGISTRY.getInstances()
      COMMANDLINELOGGER.debug("Instances loaded.")
    
      # Create main parser
      parser = argparse.ArgumentParser(prog="Machination", description='Machination utility, all your appliances belong to us.')
      rootSubparsers = parser.add_subparsers(dest="function")
      
      versionParser = rootSubparsers.add_parser('version', help='Display version')      
      
      # Parser for list command
      listParser = rootSubparsers.add_parser('list', help='List templates and instances')
      listParser.add_argument('type', help='Type to list',nargs='?', type=str, choices = ("templates","instances"))
      listParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      
      # Parser for create command
      createParser = rootSubparsers.add_parser('create', help='Create the given machine in the path')
      createParser.add_argument('template', help='Name of the template to create', type=str, choices = templates.keys())
      createParser.add_argument('name', help='Name of the machine to create', type=str)
      createParser.add_argument('--arch','-a', help='Architecture to use', type=str)
      createParser.add_argument('--provider','-p', help='Provider to use', type=str)
      createParser.add_argument('--provisioner','-n', help='Provisioner to use', type=str)
      createParser.add_argument('--osversion','-o', help='OS Version to use', type=str)
      createParser.add_argument('--guestinterface','-i', help='Network interface to add', metavar="<host_interface>,<ip_addr>[,mac_addr,hostname]", action='append', type=str)
      createParser.add_argument('--sharedfolder','-s', nargs=2, help='Shared folder between the new machine and the host', metavar=("<host folder>","<guest folder>"), action='append', type=str)
      createParser.add_argument('--no-interactive', help='Do not request for interactive configuration of optional elements (interfaces,sharedfolders)', action='store_true')
      createParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      createParser.add_argument('--force',"-f", help='Force creation by deleting an instance with same name', action='store_true')
      
            
      # Parser for destroy command
      destroyParser = rootSubparsers.add_parser('destroy', help='Destroy the given machine in the path')
      destroyParser.add_argument('names', help='Name of the machine to destroy',nargs="+",type=str, choices=instances.keys())
      destroyParser.add_argument('--force','-f', help='Do not ask for confirmation', action='store_true')
      destroyParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')

      # Parser for start command
      startParser = rootSubparsers.add_parser('start', help='Start the given machine instance')
      startParser.add_argument('names', help='Name of the machine to start', nargs="+", type=str, choices=instances.keys())
      startParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')

      # Parser for stop command
      stopParser = rootSubparsers.add_parser('stop', help='Stop the given machine instance')
      stopParser.add_argument('names', help='Name of the machine to stop', nargs="+", type=str, choices=instances.keys())
      stopParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      
      # Parser for restart command
      restartParser = rootSubparsers.add_parser('restart', help='Restart the given machine instance')
      restartParser.add_argument('names', help='Name of the machine to restart', nargs="+", type=str, choices=instances.keys())
      restartParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      
      # Parser for infos command
      infosParser = rootSubparsers.add_parser('infos', help='Get informations about a machine instance')
      infosParser.add_argument('names', help='Name of the machine instance from which infos shall be retrieved', nargs="?", type=str, choices=instances.keys())
      infosParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      
      # Parser for ssh command
      sshParser = rootSubparsers.add_parser('ssh', help='SSH to the given machine')
      sshParser.add_argument('name', help='Name of the machine to ssh in',choices=instances.keys(),type=str)
      sshParser.add_argument('--command',"-c", help='Command to execute in SSH',type=str) 
      sshParser.add_argument('--verbose',"-v", help='Verbose mode', action='store_true')
      # Parse the command
      argcomplete.autocomplete(parser)
      args = parser.parse_args()
      
      functions = {
                  "list":self.listElements,
                  "create":self.createMachineInstance,
                  "destroy":self.destroyMachineInstance,
                  "start":self.startMachineInstance,
                  "stop":self.stopMachineInstance,
                  "restart":self.restartMachineInstance,
                  "infos":self.getMachineInstanceInfos,
                  "ssh":self.sshIntoMachineInstance,
                  "version":self.displayVersion
                  }
      
      if("verbose" in args and args. verbose):
        setGlobalLogLevel(logging.DEBUG)
      else:
        setGlobalLogLevel(logging.INFO)
      
      res = 0
      if(args.function in functions.keys()):
        res = functions[args.function](args)
      
      return res

