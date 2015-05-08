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

import re
import os
import yaml
import json
import subprocess
import sys
import pwd
import shutil
import traceback
from distutils.version import LooseVersion

from machination.constants import MACHINATION_INSTALLDIR
from machination.constants import MACHINATION_USERINSTANCESDIR
from machination.constants import MACHINATION_CONFIGFILE_NAME
from machination.constants import MACHINATION_PACKERFILE_NAME

from machination.provisioners import Provisioner
from machination.providers import Provider

from machination.globals import MACHINE_TEMPLATE_REGISTRY

from machination.enums import Architecture

from machination.exceptions import PathNotExistError
from machination.exceptions import InvalidArgumentValue
from machination.exceptions import InvalidYAMLException
from machination.exceptions import InvalidMachineTemplateException

from machination.helpers import accepts
from machination.loggers import CORELOGGER

# #
# Class representing a network interface
#
class NetworkInterface(yaml.YAMLObject):
    yaml_tag = "!NetworkInterface"
    _ipAddr = None
    _macAddr = None
    _hostname = None
    _hostInterface = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, str, str, None)
    def __init__(self, ipAddr, macAddr, hostInterface, hostname="None"):
      # Check each given argument
      # IP Address can be also dhcp
      if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$", ipAddr):
        self._ipAddr = ipAddr
      else:
        raise InvalidArgumentValue("ipAddr",ipAddr)
      if re.match("^([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})$", macAddr):
        self._macAddr = macAddr
      else:
        raise InvalidArgumentValue("macAddr",macAddr)

      if hostname == None or (type(hostname) is str and re.match("^([0-9a-zA-Z]*)$", hostname)):
        self._hostname = hostname
      else:
        raise InvalidArgumentValue("hostname",hostname)
        
      if hostInterface == None or (type(hostInterface) is str):
        self._hostInterface = hostInterface
      else:
        raise InvalidArgumentValue("hostInterface",hostInterface)


    # ##
    # Simple getters
    # ##
    def getIPAddr(self):
      return self._ipAddr

    def getMACAddr(self):
      return self._macAddr
      
    def getHostInterface(self):
      return self._hostInterface

    def getHostname(self):
      if self._hostname == None:
        return ""
      else:
        return self._hostname

    # ##
    # ToString method
    # ##
    def __str__(self):
      res = ""
      if self._hostname != None :
          res = self._hostname + "|"
      return res + self.getIPAddr() + "|" + self.getMACAddr() + "|" + self.getHostInterface()

    # ##
    # Function to dump a network interface to yaml
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                         "ip_addr" : data.getIPAddr(),
                         "mac_addr" : data.getMACAddr(),
                         "host_interface" : data.getHostInterface()
                         }
      # Only dump the hostname if it has been set
      if data.getHostname() != None:
          representation["hostname"] = data.getHostname()
      return dumper.represent_mapping(data.yaml_tag, representation)

    # ##
    # Function to retrieve an object from yaml
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      # Need to check if IP Address or MAC Address are available
      if not "ip_addr" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing IP address")

      if not "mac_addr" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing MAC address")
      
      if not "host_interface" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing Host interface")

      hostname = None
      if "hostname" in representation.keys():
        hostname = representation["hostname"]

      return NetworkInterface(representation["ip_addr"],  representation["mac_addr"], representation["host_interface"], hostname)
    
# ##
# Class representing a sync folder between host and guest
# ##
class SharedFolder(yaml.YAMLObject):
    yaml_tag = "!SharedFolder"
    _hostDir = None
    _guestDir = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, str)
    def __init__(self, host_dir, guest_dir):
      # Path on the host must exist
      if os.path.exists(host_dir):
        self._hostDir = host_dir
      else:
        raise PathNotExistError(host_dir)
      if re.match("^(\/.*)$",guest_dir):
        self._guestDir = guest_dir
      else:
        raise InvalidArgumentValue("guest_dir",guest_dir)

    # ##
    # Simple getters
    # ##
    def getHostDir(self):
      return self._hostDir

    def getGuestDir(self):
      return self._guestDir

    # ##
    # ToString function
    # ##
    def __str__(self):
      return self._hostDir + " => " + self._guestDir

    # ##
    # Function to dump the object as YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                         "host_dir" : data.getHostDir(),
                         "guest_dir" : data.getGuestDir()
                         }
      return dumper.represent_mapping(data.yaml_tag, representation)

    # ##
    # Function to create a sharedfolder from yaml
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      # A Shared folder shall have a host_dir and a guest_dir
      if not "host_dir" in representation.keys():
          raise InvalidYAMLException("Invalid shared folder: missing host directory")

      if not "guest_dir" in representation.keys():
          raise InvalidYAMLException("Invalid shared folder: missing guest directory")

      return SharedFolder(representation["host_dir"],
                          representation["guest_dir"])

# ##
# Class representing a machine template
# ##
class MachineTemplate(yaml.YAMLObject):
    yaml_tag = '!MachineTemplate'
    _path = None
    _name = None
    _provisioners = []
    _providers = []
    _osVersions = []
    _archs = []
    _guestInterfaces = []
    _version = None
    _comments = ""
    _roles = []

    # ##
    # Constructor
    # ##
    @accepts(None, str, list, list, list,list, None,str,list)
    def __init__(self, path, archs, osVersions , providers, provisioners, guestInterfaces,comments,roles):
      # Checking the arguments

      if not os.path.exists(path):
        raise InvalidArgumentValue("Template path",path)

      if len(archs) == 0:
        raise InvalidMachineTemplateException("Invalid number of architectures")
      else:
        for arch in archs:
          if type(arch) is not Architecture:
            raise InvalidMachineTemplateException("Invalid architecture")

      if len(providers) == 0:
        raise InvalidMachineTemplateException("Invalid number of providers")
      else:
        for p in providers:
          if not isinstance(p,Provider):
            raise InvalidMachineTemplateException("Invalid provider")

      if len(provisioners) == 0:
        raise InvalidMachineTemplateException("Invalid number of provisioners")
      else:
        for p in provisioners:
          if not isinstance(p,Provisioner):
            raise InvalidMachineTemplateException("Invalid provisioner")

      if len(osVersions) == 0:
        raise InvalidMachineTemplateException("Invalid number of os versions")
      
      if len(roles) == 0:
        raise InvalidMachineTemplateException("Invalid number of roles")
      else:
        for r in roles:
          if not isinstance(r,str):
            raise InvalidMachineTemplateException("Invalid role")
      
      fileName = os.path.basename(path)
      nameAndVersion = os.path.splitext(fileName)[0]
      versionIdx = nameAndVersion.find('.')
      self._name = nameAndVersion[0:versionIdx]
      self._version = LooseVersion(nameAndVersion[versionIdx+1:])
      self._path = path
      self._archs = archs
      self._osVersions = osVersions
      self._providers = providers
      self._provisioners = provisioners
      self._guestInterfaces = guestInterfaces
      self._roles = roles
      if type(comments) is str:
        self._comments = comments

    # ##
    # Simple getters
    # ##
    def getPath(self):
      return self._path

    def getArchs(self):
      return self._archs

    def getProviders(self):
      return self._providers

    def getProvisioners(self):
      return self._provisioners

    def getOsVersions(self):
      return self._osVersions

    def getGuestInterfaces(self):
      return self._guestInterfaces

    def getVersion(self):
      return self._version
    
    def getName(self):
      return self._name
    
    def getComments(self):
      return self._comments
    
    def getRoles(self):
      return self._roles
    
    def __str__(self):
      return self.getName()+":"+self.getVersion()

    # ##
    # Function to dump the object into YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                          "path" : data.getPath(),
                          "archs" : data.getArchs(),
                          "os_versions" : str(data.getOsVersions()),
                          "providers" : str(data.getProviders()),
                          "provisioners" : str(data.getProvisioners()),
                          "guest_interfaces" : data.getGuestInterfaces(),
                          "comments" : data.getComments(),
                          "roles" : data.getRoles()
                          }
      node = dumper.represent_mapping(data.yaml_tag, representation)
      return node

    # ##
    # Function to create a template from YAML
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      archs = []
      # Check if architectures are present in the template
      if "archs" in representation.keys() and type(representation["archs"]) is list:
          for p in representation["archs"]:
              archs.append(Architecture.fromString(p))

      providers = []
      # Check if providers are present in the template
      if "providers" in representation.keys() and type(representation["providers"]) is list:
          for p in representation["providers"]:
              providers.append(Provider.fromString(p)())

      provisioners = []
      # Check if provisioners are present in the template
      if "provisioners" in representation.keys() and type(representation["provisioners"]) is list:
          for p in representation["provisioners"]:
              provisioners.append(Provisioner.fromString(p)())

      osVersions = None
      # Check if osVersions are present in the template
      if "os_versions" in representation.keys() and type(representation["os_versions"]) is list:
          osVersions = representation["os_versions"]

      guestInterfaces = 0
      if "guest_interfaces" in representation.keys():
          guestInterfaces = representation["guest_interfaces"]

      roles = []
      if "roles" in representation.keys():
          roles = representation["roles"]

      comments = ""
      if "comments" in representation.keys():
          comments = representation["comments"]

      return MachineTemplate(loader.stream.name,
                             archs,
                             osVersions,
                             providers,
                             provisioners,
                             guestInterfaces,
                             comments,
                             roles)

# ##
# Class representing a MachineInstance instance
# ##
class MachineInstance(yaml.YAMLObject):
    yaml_tag = '!MachineInstance'
    _name = None
    _template = None
    _provisioner = None
    _provider = None
    _osVersion = None
    _guestInterfaces = None
    _arch = None
    _sharedFolders = None
    _packerFile = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, MachineTemplate, Architecture, str, Provider, Provisioner, list, list)
    def __init__(self, name, template, arch, osVersion, provider, provisioner, guestInterfaces, sharedFolders):
      # Check the arguments
      if len(osVersion) == 0:
        raise InvalidArgumentValue("osVersion",osVersion)

      if len(name) == 0:
        raise InvalidArgumentValue("name",name)
        
      # Manually check the type of list elements
      for i in guestInterfaces:
        if not type(i) is NetworkInterface:
          raise InvalidArgumentValue("guest_interfaces",i)

      for f in sharedFolders:
        if not type(f) is SharedFolder:
          raise InvalidArgumentValue("shared_folder",f)
      self._name = name
      self._template = template
      self._arch = arch
      self._osVersion = osVersion
      self._provider = provider
      self._provisioner = provisioner
      self._guestInterfaces = guestInterfaces
      self._sharedFolders = sharedFolders
      self._packerFile = {}

    # ##
    # Simple getters
    # ##
    def getPath(self):
      return os.path.join(MACHINATION_USERINSTANCESDIR, self.getName())

    def getPackerFile(self):
      return self._packerFile
    
    # ##
    # Function to generate the file attached to the instance
    # ##
    def create(self):
      # If the machine does not exist yet
      if not os.path.exists(self.getPath()):
        # Create its folder and copy the Vagrant file
        os.makedirs(self.getPath())
        shutil.copy(os.path.join(MACHINATION_INSTALLDIR, "share", "machination", "vagrant", "Vagrantfile"), os.path.join(self.getPath(), "Vagrantfile"))
        try:
          # Create the machine config file
          configFile = yaml.dump(self)
          openedFile = open(os.path.join(self.getPath(), MACHINATION_CONFIGFILE_NAME), "w+")
          openedFile.write(configFile)
          openedFile.close()
          # Generate the file related to the provisioner and the provider
          variables = {}
          variables["os_version"] = self.getOsVersion()
          variables["architecture"] = str(self.getArch())
          variables["template_name"] = self.getTemplate().getName()
          variables["template_version"] = str(self.getTemplate().getVersion())
          self.getPackerFile()["variables"] = variables
          self.getPackerFile()["builders"] = []
          self.getPackerFile()["provisioners"] = []
          self.getPackerFile()["post-processors"] = []
    
          self.getProvider().generateFilesFor(self)
          self.getProvisioner().generateFilesFor(self)
          
          outfile = open(os.path.join(self.getPath(),MACHINATION_PACKERFILE_NAME),"w")
          json.dump(self.getPackerFile(),outfile,indent=2)
          outfile.close()
          self.pack()
          
        except Exception as e:
          shutil.rmtree(self.getPath())
          CORELOGGER.debug(traceback.format_exc())
          raise e
      else:
        shutil.rmtree(self.getPath())
        # Raise an error about the fact the machine already exists
        raise RuntimeError("MachineInstance instance '{0}' already exists".format(self.getPath()))

    def pack(self):
      # If the machine does not exist yet
      if os.path.exists(self.getPath()):
        if self.getProvider().needsProvision(self):
          CORELOGGER.debug("Image needs provisioning, starting packer...")
          cmd = "packer build ./{0}".format(MACHINATION_PACKERFILE_NAME)
          
          # Fire up the vagrant machine
          p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
          p.communicate()[0]
          returnCode = p.returncode
          if returnCode != 0:
            raise RuntimeError("Error while creating packing '{0}'".format(self.getName()));
      else:
            raise RuntimeError("Error while packing machine '{0}'".format(self.getName()));
    # ##
    # Simple getters
    # ##
    def getName(self):
      return self._name

    def getArch(self):
      return self._arch

    def getProvisioner(self):
      return self._provisioner

    def getProvider(self):
      return self._provider

    def getSharedFolders(self):
      return self._sharedFolders

    def getTemplate(self):
      return self._template
    
    def getGuestInterfaces(self):
      return self._guestInterfaces

    def getOsVersion(self):
      return self._osVersion

    def __str__(self):
      return self.getName()

    # ##
    # Function to start an instance
    # This function must be ran as root as some action in the the provisioner or the provider may require a root access
    # ##
    def start(self):
      # Fire up the vagrant machine
      self.pack()
      p = subprocess.Popen("vagrant up", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
      p.communicate()[0]
      if p.returncode != 0:
        raise RuntimeError("Error while starting machine instance: '{0}'".format(self.getName()));

    # ##
    # Function to destroy an instance
    # ##
    def destroy(self):
      # Destroy the vagrant machine
      p = subprocess.Popen("vagrant destroy -f", shell=True, stdout=subprocess.PIPE, cwd=self.getPath())
      p.wait()
      if p.returncode != 0:
        raise RuntimeError("Error while destroying machine instance '{0}'".format(self.getName()));
      shutil.rmtree(self.getPath())

    # ##
    # Function to stop an instance
    # ##
    def stop(self):
      p = subprocess.Popen("vagrant halt", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
      p.communicate()[0]
      if p.returncode != 0:
        raise RuntimeError("Error while stopping machine instance: '{0}'".format(self.getName()));

    # ##
    # ##
    def getInfos(self):
      i = 0
      output =  "  Name: {0}\n".format(self.getName())
      output += "  Architecture: {0}\n".format(self.getArch())
      output += "  Provisioner: {0}\n".format(self.getProvisioner())
      output += "  Provider: {0}\n".format(self.getProvider())
      p = subprocess.Popen("vagrant ssh-config", shell=True,  stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=self.getPath())
      out = p.communicate()[0]
      if p.returncode == 0:
        ipAddrSearch = re.search("HostName (.*)",out)
        if ipAddrSearch != None :
          output += "  Primary IPAddress of the container: {0}\n".format(ipAddrSearch.group(1))
      if(self.isStarted()):
          output += "  State: Running\n"
      else:
          output += "  State: Stopped\n"
      if len(self.getGuestInterfaces()) != 0 :
        output +="  Network interfaces:\n"
        for intf in self.getGuestInterfaces():
          output += "  - Name: eth{0}\n".format(i)
          output += "    IPAddress: {0}\n".format(intf.getIPAddr())
          output += "    MACAddress: {0}\n".format(intf.getMACAddr())
          output += "    Host interface: {0}\n".format(intf.getHostInterface())
          if intf.getHostname() != None:
            output += "    Hostname: {0}\n".format(intf.getHostname())
          i += 1
      return output

    # ##
    # Function to ssh to an instance
    # ##
    def ssh(self):
      if(self.isStarted()):
        # Start vagrant ssh to ssh into the instance
        val = subprocess.Popen("vagrant ssh", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
        # get the output of the machine
        while True:
            out = val.stderr.read(1)
            if out == '' and val.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
      else:
        raise RuntimeError("Machine instance not started")

    def isStarted(self):
      p = subprocess.Popen("vagrant status", shell=True,  stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=self.getPath())
      isStarted = False
      out = p.communicate()[0]
      isStarted = (isStarted or (re.search("(.*)machination-{0}(.*)running(.*)".format(self.getName()),out) != None)) 
      if p.returncode == 0 and isStarted:
        return True
      else:
        return False
      
    # ##
    # Function to dump the object to YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                               "template" : "{0}:{1}".format(data.getTemplate().getName(),data.getTemplate().getVersion()),
                               "arch" : str(data.getArch()),
                               "os_version" : str(data.getOsVersion()),
                               "provider" : str(data.getProvider()),
                               "provisioner" : str(data.getProvisioner()),
                               "guest_interfaces" : data.getGuestInterfaces(),
                               "shared_folders" :  data.getSharedFolders(),
                               }
        node = dumper.represent_mapping(data.yaml_tag, representation)
        return node

    # ##
    # Function to create an object from YAML
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)

        # Retrieve the elements to create an instance
        arch = None
        if "arch" in representation.keys():
            arch = Architecture.fromString(representation["arch"])

        provider = None
        if "provider" in representation.keys():
            provider = Provider.fromString(representation["provider"])()

        provisioner = None
        if "provisioner" in representation.keys():
            provisioner = Provisioner.fromString(representation["provisioner"])()

        name = os.path.basename(os.path.dirname(loader.stream.name))

        template = None
        if "template" in representation.keys():
          template = MACHINE_TEMPLATE_REGISTRY.getTemplates()[representation["template"]]

        osVersion = None
        if "os_version" in representation.keys():
            osVersion = representation["os_version"]

        guestInterfaces = []
        if "guest_interfaces" in representation.keys():
            guestInterfaces = representation["guest_interfaces"]

        sharedFolders = []
        if "shared_folders" in representation.keys():
            sharedFolders = representation["shared_folders"]
        
        return MachineInstance(name,
                                   template,
                                   arch,
                                   osVersion,
                                   provider,
                                   provisioner,
                                   guestInterfaces,
                                   sharedFolders)
