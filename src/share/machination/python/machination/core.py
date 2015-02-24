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
import subprocess
import sys
import pwd
import shutil

from machination.constants import MACHINATION_INSTALLDIR
from machination.constants import MACHINATION_USERDIR

from machination.enums import Provider
from machination.enums import Provisioner
from machination.enums import Architecture

from machination.exceptions import PathNotExistError
from machination.exceptions import InvalidArgumentValue
from machination.exceptions import InvalidYAMLException
from machination.exceptions import InvalidMachineTemplateException

from machination.registries import MachineTemplateRegistry
from machination.helpers import accepts

import machination.helpers

##
# Class representing a network interface
#
class NetworkInterface(yaml.YAMLObject):
    yaml_tag = "!NetworkInterface"
    _ipAddr = None
    _macAddr = None
    _hostname = None

    ###
    # Constructor
    ###
    @accepts(None,str,str,str)
    def __init__(self,ipAddr, macAddr,hostname=None):
        # Check each given argument
        # IP Address can be also dhcp
        if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$",ipAddr):
            self._ipAddr = ipAddr
        else:
            raise InvalidArgumentValue("ipAddr")
        if re.match("^([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})$",macAddr):
            self._macAddr = macAddr
        else:
            raise InvalidArgumentValue("macAddr")

        self._ipAddr = ipAddr
        self._macAddr = macAddr

        # Hotname argument is not mandatory
        self._hostname = hostname

    ###
    # Simple getters
    ###
    def getIPAddr(self):
        return self._ipAddr

    def getMACAddr(self):
        return self._macAddr

    def getHostname(self):
        if self._hostname == None:
            return ""
        else:
            return self._hostname

    ###
    # ToString method
    ###
    def __str__(self):
        res = ""
        if self._hostname != None :
            res = self._hostname + "|"
        return res + self.getIPAddr()+"|"+self.getMACAddr()

    ###
    # Function to dump a network interface to yaml
    ###
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "ip_addr" : data.getIPAddr(),
                           "mac_addr" : data.getMACAddr()
                           }
        # Only dump the hostname if it has been set
        if data.getHostname()!=None:
            representation["hostname"] = data.getHostname()
        return dumper.represent_mapping(data.yaml_tag,representation)

    ###
    # Function to retrieve an object from yaml
    ###
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        # Need to check if IP Address or MAC Address are available
        if not "ip_addr" in representation.keys():
            raise InvalidYAMLException("Invalid Network Interface: Missing IP address")

        macAddr = None
        if not "mac_addr" in representation.keys():
            macAddr = machination.helpers.randomMAC()
        else:
            macAddr = representation["mac_addr"]
            
        hostname = None
        if "hostname" in representation.keys():
            hostname=representation["hostname"]

        return NetworkInterface(representation["ip_addr"],macAddr,hostname)

###
# Class representing a sync folder between host and guest
###
class SyncedFolder(yaml.YAMLObject):
    yaml_tag = "!SyncedFolder"
    _hostDir = None
    _guestDir = None

    ###
    # Constructor
    ###
    @accepts(None,str,str)
    def __init__(self,host_dir,guest_dir):
        # Path on the host must exist
        if not os.path.exists(host_dir):
            raise PathNotExistError(host_dir)
        self._hostDir = host_dir
        self._guestDir = guest_dir

    ###
    # Simple getters
    ###
    def getHostDir(self):
        return self._hostDir

    def getGuestDir(self):
        return self._guestDir

    ###
    # ToString function
    ###
    def __str__(self):
        return self._hostDir + " => " + self._guestDir

    ###
    # Function to dump the object as YAML
    ###
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "host_dir" : data.getHostDir(),
                           "guest_dir" : data.getGuestDir()
                           }
        return dumper.represent_mapping(data.yaml_tag,representation)

    ###
    # Function to create a syncfolder from yaml
    ###
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        # A Synced folder shall have a host_dir and a guest_dir
        if not "host_dir" in representation.keys():
            raise InvalidYAMLException("Invalid Synced folder: missing host directory")

        if not "guest_dir" in representation.keys():
            raise InvalidYAMLException("Invalid Synced folder: missing guest directory")

        return SyncedFolder(representation["host_dir"],
                            representation["guest_dir"])

###
# Class representing a machine template
###
class MachineTemplate(yaml.YAMLObject):
    yaml_tag = '!MachineTemplate'
    path = None
    provisioners = []
    providers = []
    os_versions = []
    archs = []
    guest_interfaces = []

    ###
    # Constructor
    ###
    @accepts(None,str,list,list,list,list)
    def __init__(self, path, archs, os_versions ,providers, provisioners, guest_interfaces):
        # Checking the arguments
        if not os.path.exists(path):
            raise InvalidMachineTemplateException("Unknown template path")

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
                if type( p) is not Provider:
                    raise InvalidMachineTemplateException("Invalid provider")

        if len(provisioners) == 0:
            raise InvalidMachineTemplateException("Invalid number of provisioners")
        else:
            for p in provisioners:
                if type(p) is not Provisioner:
                    raise InvalidMachineTemplateException("Invalid provisioner")

        if len(os_versions) == 0:
            raise InvalidMachineTemplateException("Invalid number of os versions")

        for i in guest_interfaces:
            if type(i) is not NetworkInterface:
                raise InvalidMachineTemplateException("Invalid guest interface")

        self.path = path
        self.archs = archs
        self.os_versions = os_versions
        self.providers = providers
        self.provisioners = provisioners
        self.guest_interfaces = guest_interfaces

    ###
    # Simple getters
    ###
    def getName(self):
        fileName = os.path.basename(self.path)
        return os.path.splitext(fileName)[0]

    def getPath(self):
        return self.path

    def getArchs(self):
        return self.archs

    def getProviders(self):
        return self.providers

    def getProvisioners(self):
        return self.provisioners

    def getOsVersions(self):
        return self.os_versions

    def getGuestInterfaces(self):
        return self.guest_interfaces

    ###
    # Function to dump the object into YAML
    ###
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                            "path" : data.path,
                            "archs" : data.archs,
                            "os_versions" : str(data.os_versions),
                            "providers" : str(data.providers),
                            "provisioners" : str(data.provisioners),
                            "guest_interfaces" : data.guest_interfaces,
                            }
        node = dumper.represent_mapping(data.yaml_tag,representation)
        return node

    ###
    # Function to create a template from YAML
    ###
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        archs = []
        # Check if architectures are present in the template
        if "archs" in representation.keys() and type(representation["archs"]) is list:
            for p in representation["archs"]:
                archs.append(Architecture.fromString(p))

        providers = []
        # Check if providers are present in the template
        if "providers" in representation.keys() and type(representation["providers"]) is list:
            for p in representation["providers"]:
                providers.append(Provider.fromString(p))

        provisioners = []
        # Check if provisioners are present in the template
        if "provisioners" in representation.keys() and type(representation["provisioners"]) is list:
            for p in representation["provisioners"]:
                provisioners.append(Provisioner.fromString(p))

        os_versions = None
        # Check if osVersions are present in the template
        if "os_versions" in representation.keys() and type(representation["os_versions"]) is list:
            os_versions = representation["os_versions"]

        guest_interfaces = []
        if "guest_interfaces" in representation.keys() and type(representation["guest_interfaces"]) is list:
            guest_interfaces = representation["guest_interfaces"]

        return MachineTemplate(loader.stream.name,
                               archs,
                               os_versions,
                               providers,
                               provisioners,
                               guest_interfaces)

###
# Class representing a Machine instance
###
class MachineInstance(yaml.YAMLObject):
    yaml_tag = '!MachineInstance'
    name = None
    template = None
    provisioner = None
    provider = None
    os_version = None
    host_interface = None
    guest_interfaces  = None
    arch = None
    synced_folders = None

    ###
    # Constructor
    ###
    @accepts(None,str,MachineTemplate,Architecture,str,Provider,Provisioner,str,list,list)
    def __init__(self, name, template, arch,os_version,provider, provisioner, host_interface, guest_interfaces,synced_folders):

        # Check the arguments
        if len(os_version) == 0:
            raise InvalidArgumentValue("osVersion")

        if len(name) == 0:
            raise InvalidArgumentValue("name")

        # The host_interface must be of the form <Alphanumeric><Numeric>
        if not re.match("[a-z]+[0-9]+", host_interface):
            raise InvalidArgumentValue("host_interface")

        # Manually check the type of list elements
        for i in guest_interfaces:
            if not type(i) is NetworkInterface:
                raise InvalidArgumentValue("network_interface")

        for f in synced_folders:
            if not type(f) is SyncedFolder:
                raise InvalidArgumentValue("synced_folder")
        self.name = name
        self.template = template
        self.arch = arch
        self.os_version = os_version
        self.provider = provider
        self.provisioner = provisioner
        self.guest_interfaces = guest_interfaces
        self.host_interface = host_interface
        self.synced_folders = synced_folders

    ###
    # Simple getters
    ###
    def getPath(self):
        return os.path.join(MACHINATION_USERDIR,"instances",self.getName())

    ###
    # Function to generate the file attached to the instance
    ###
    def generateFiles(self):
        # If the machine does not exist yet
        if not os.path.exists(self.getPath()):
            # Create its folder and copy the Vagrant file
            os.makedirs(self.getPath())
            shutil.copy(os.path.join(MACHINATION_INSTALLDIR,"share","machination","vagrant","Vagrantfile"),os.path.join(self.getPath(),"Vagrantfile"))

            # Generate the file related to the provisioner
            generator = Provisioner.getFileGenerator(self.getProvisioner())
            generator.generateFiles(self.getTemplate(),self.getPath())
            # Create the machine config file
            configFile = yaml.dump(self)
            openedFile = open(os.path.join(self.getPath(),"config.yml"),"w+")
            openedFile.write(configFile)
            openedFile.close()
        else:
            # Raise an error about the fact the machine already exists
            raise RuntimeError("Machine {0} already exists".format(self.getPath()))

    ###
    # Simple getters
    ###
    def getName(self):
        return self.name

    def getProvisioner(self):
        return self.provisioner

    def getSharedFolders(self):
        return self.shared_folders

    def getTemplate(self):
        return self.template

    ###
    # Function to start an instance
    # This function must be ran as root as some action in the the provisioner or the provider may require a root access
    ###
    def start(self):
        # Get the real user behind the sudo
        pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
        # Set the install dir of machination as an environment variable (this will be used by vagrant
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        # Fire up the vagrant machine
        subprocess.Popen("vagrant up", shell=True, stdout=subprocess.PIPE,env=instanceEnv,cwd=self.getPath()).stdout.read()
        # change the owner of the created files
        os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)
        for root, dirs, files in os.walk(self.getPath()):
            for d in dirs:
                os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
            for f in files:
                os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)

    ###
    # Function to destroy an instance
    ###
    def destroy(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        # Destroy the vagrant machine
        instanceEnv = os.environ.copy()
        subprocess.Popen("vagrant destroy -f", shell=True, stdout=subprocess.PIPE, env=instanceEnv, cwd=self.getPath()).stdout.read()
        shutil.rmtree(self.getPath())

    ###
    # Function to stop an instance
    ###
    def stop(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        subprocess.Popen("vagrant halt", shell=True, stdout=subprocess.PIPE, env=instanceEnv,cwd=self.getPath()).stdout.read()

    ###
    # Function to ssh to an instance
    ###
    def ssh(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        # Start vagrant ssh to ssh into the instance
        instanceEnv = os.environ.copy()
        val = subprocess.Popen("vagrant ssh", shell=True, env=instanceEnv, stderr=subprocess.PIPE, cwd=self.getPath())
        # get the output of the machine
        while True:
            out = val.stderr.read(1)
            if out == '' and val.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()

    ###
    # Function to dump the object to YAML
    ###
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                               "name" : data.name,
                               "template" : data.template.getName(),
                               "arch" : str(data.arch),
                               "os_version" : str(data.os_version),
                               "provider" : str(data.provider),
                               "provisioner" : str(data.provisioner),
                               "host_interface" : data.host_interface,
                               "guest_interfaces" : data.guest_interfaces,
                               "synced_folders" :  data.synced_folders,
                               }
        node = dumper.represent_mapping(data.yaml_tag,representation)
        return node

    ###
    # Function to create an object from YAML
    ###
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)

        # Retrieve the elements to create an instance
        arch = None
        if "arch" in representation.keys():
            arch = Architecture.fromString(representation["arch"])

        provider = None
        if "provider" in representation.keys():
            provider = Provider.fromString(representation["provider"])

        provisioner = None
        if "provisioner" in representation.keys():
            provisioner = Provisioner.fromString(representation["provisioner"])

        name = os.path.basename(os.path.dirname(loader.stream.name))

        template = None
        if "template" in representation.keys():
            # Retrieve the template from the registry
            templateReg = MachineTemplateRegistry([os.path.join(MACHINATION_INSTALLDIR,'share','machination', 'templates'),os.path.join(MACHINATION_USERDIR, 'templates') ])
            template =   templateReg.getTemplates()[representation["template"]]

        os_version = None
        if "os_version" in representation.keys():
            os_version = representation["os_version"]

        host_interface = None
        if "host_interface" in representation.keys():
            host_interface = representation["host_interface"]

        guest_interfaces = []
        if "guest_interfaces" in representation.keys():
            guest_interfaces = representation["guest_interfaces"]

        synced_folders = []
        if "sync_folders" in representation.keys():
            synced_folders = representation["sync_folders"]

        return MachineInstance(name,
                                   template,
                                   arch,
                                   os_version,
                                   provider,
                                   provisioner,
                                   host_interface,
                                   guest_interfaces,
                                   synced_folders)
