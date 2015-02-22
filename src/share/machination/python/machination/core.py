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

from machination.helpers import accepts

class NetworkInterface(yaml.YAMLObject):
    yaml_tag = "!NetworkInterface"
    _ipAddr = None
    _macAddr = None
    _hostname = None

    @accepts(None,str,str,str)
    def __init__(self,ipAddr, macAddr,hostname=""):
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
        self._hostname = hostname

    def getIPAddr(self):
        return self._ipAddr
    
#     @accepts(None,str)
#     def setIPAddr(self,val):
#         if re.match(val,"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$"):
#             self._ipAddr = val
#         else:
#             raise ArgumentValueError("ipAddr","Invalid IPAddress")
        
    def getMACAddr(self):
        return self._macAddr
    
#     @accepts(None,str)
#     def setMACAddr(self,val):
#         if re.match(val,"^([a-fA-F0-9]{2}:){5}([a-fA-F0-9]{2})$"):
#             self._macAddr = val
#         else:
#             raise ArgumentValueError("ipAddr","Invalid IPAddress")
        
    def getHostname(self):
        return self._hostname
    
#     @accepts(None,str)
#     def setHostname(self,val):
#         self._hostname = val

    def __str__(self):
        res = ""
        if self._hostname != None :
            res = self._hostname + "|"
        return res + self.getIPAddr()+"|"+self.getMACAddr()
    
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "ip_addr" : data.getIPAddr(),
                           "mac_addr" : data.getMACAddr()
                           }
        if data.getHostname()!=None:
            representation["hostname"] = data.getHostname()
        return dumper.represent_mapping(data.yaml_tag,representation)

    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        if not "ip_addr" in representation.keys():
            raise InvalidMachineTemplateError("Invalid IP address")
        
        if not "mac_addr" in representation.keys():
            raise InvalidMachineTemplateError("Invalid MAC address")
    
        hostname = None
        if "hostname" in representation.keys():
            hostname=representation["hostname"]
            
        return NetworkInterface(representation["ip_addr"],representation["mac_addr"],hostname)

class SyncedFolder(yaml.YAMLObject):
    yaml_tag = "!SyncedFolder"
    _hostDir = None
    _guestDir = None

    @accepts(None,str,str)
    def __init__(self,host_dir,guest_dir):
        if not os.path.exists(host_dir):
            raise PathNotExistError(host_dir)
        
        self._hostDir = host_dir
        self._guestDir = guest_dir

    def getHostDir(self):
        return self._hostDir
        
    def getGuestDir(self):
        return self._guestDir
    
#     def setGuestDir(self,val):
#         self._guestDir = val

    def __str__(self):
        return self._hostDir + " => " + self._guestDir
    
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "host_dir" : data.getHostDir(),
                           "guest_dir" : data.getGuestDir()
                           }
        return dumper.represent_mapping(data.yaml_tag,representation) 

    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        
        if not "host_dir" in representation.keys():
            raise InvalidMachineTemplateError("Invalid host directory")
        
        if not "guest_dir" in representation.keys():
            raise InvalidMachineTemplateError("Invalid guest directory")              
        
        return SyncedFolder(representation["host_dir"],
                            representation["guest_dir"])
        
        
class InvalidMachineTemplateError:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)
    
class MachineTemplate(yaml.YAMLObject):
    yaml_tag = '!MachineTemplate'
    path = None
    provisioners = []
    providers = []
    os_versions = []
    archs = []
    guest_interfaces = []
    
    @accepts(None,str,list,list,list,list)
    def __init__(self, path, archs, os_versions ,providers, provisioners, guest_interfaces):
        if not os.path.exists(path):
            raise InvalidMachineTemplateError("Invalid path")
        
        if len(archs) == 0:
            raise InvalidMachineTemplateError("Invalid number of architecture")
        else:
            for arch in archs:
                if type(arch) is not Architecture:
                    raise InvalidMachineTemplateError("invalid architecture")
            
        if len(providers) == 0:
            raise InvalidMachineTemplateError("Invalid number of providers")
        else:
            for p in providers:
                if type( p) is not Provider:
                    raise InvalidMachineTemplateError("invalid provider")

        if len(provisioners) == 0:
            raise InvalidMachineTemplateError("Invalid number of provisioners")
        else:
            for p in provisioners:
                if type(p) is not Provisioner:
                    raise InvalidMachineTemplateError("invalid provisioner")

        if len(os_versions) == 0:
            raise InvalidMachineTemplateError("Invalid number of os versions")
        
        for i in guest_interfaces:
            if type(i) is not NetworkInterface:
                raise InvalidMachineTemplateError("Invalid guest interface")
        
        self.path = path
        self.archs = archs
        self.os_versions = os_versions
        self.providers = providers
        self.provisioners = provisioners
        self.guest_interfaces = guest_interfaces
        
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
    
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)
        archs = []
        if "archs" in representation.keys() and type(representation["archs"]) is list:
            for p in representation["archs"]:
                if p in (Architecture.__members__).keys():                
                    archs.append(Architecture[p])
                   
        providers = []
        if "providers" in representation.keys() and type(representation["providers"]) is list:
            for p in representation["providers"]:
                if p in (Provider.__members__).keys():
                    providers.append(Provider[p])
                
        provisioners = []
        if "provisioners" in representation.keys() and type(representation["provisioners"]) is list:
            for p in representation["provisioners"]:
                if p in (Provisioner.__members__).keys():
                    provisioners.append(Provisioner[p])
        
        os_versions = None
        if "os_versions" in representation.keys() and type(representation["os_versions"]) is list:
            os_versions = representation["os_versions"]
            
        guest_interfaces = None
        if "guest_interfaces" in representation.keys() and type(representation["guest_interfaces"]) is list:
            guest_interfaces = representation["guest_interfaces"]
        return MachineTemplate(loader.stream.name,                
                               archs, 
                               os_versions,                                
                               providers,
                               provisioners,  
                               guest_interfaces)

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
    
    @accepts(None,str,str,Architecture,str,Provider,Provisioner,str,list,list)
    def __init__(self, name, template, arch,os_version,provider, provisioner, host_interface, guest_interfaces,synced_folders):                
        if len(template) == 0:
            raise InvalidArgumentValue("template")
        
        if len(os_version) == 0:
            raise InvalidArgumentValue("osVersion")
    
        if len(name) == 0:
            raise InvalidArgumentValue("name")
       
        if not re.match("[a-z]+[0-9]+", host_interface):
            raise InvalidArgumentValue("host_interface")
        
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
   
                
    def getPath(self):
        return os.path.join(MACHINATION_USERDIR,"instances",self.getName())
    
    def generateFiles(self):
        if not os.path.exists(self.getPath()):
            os.makedirs(self.getPath())
            shutil.copy(os.path.join(MACHINATION_INSTALLDIR,"share","machination","vagrant","Vagrantfile"),os.path.join(self.getPath(),"Vagrantfile"))
        else:            
            raise RuntimeError("Machine {0} already exists".format(self.getPath()))

        if self.getProvisioner() == Provisioner.Ansible:
            generator = Provisioner.getFileGenerator(self.getProvisioner())
            generator.generateFiles(self.getTemplate(),self.getPath())
        else:
            raise RuntimeError("Unsupported provisioner {0}",self(self.getProvisioner()))
                        
        configFile = yaml.dump(self)
        openedFile = open(os.path.join(self.getPath(),"config.yml"),"w+")
        openedFile.write(configFile)
        openedFile.close()
        
#         pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
#         os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)
#         for root, dirs, files in os.walk(self.getPath()):  
#             for d in dirs:  
#                 os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
#             for f in files:
#                 os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)
#                     
    def getName(self):
        return self.name
            
            
    def getProvisioner(self):
        return self.provisioner
    
    def getSharedFolders(self):
        return self.shared_folders
    
    def getTemplate(self):
        return self.template
    
#     def setSharedFolders(self,val):
#         self.shared_folders = val
#  
    def start(self):
        pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR        
        instanceEnv = os.environ.copy()
        #subprocess.Popen("vagrant up", shell=True, preexec_fn=demote(pw_record.pw_uid, pw_record.pw_gid), stdout=subprocess.PIPE, env=instanceEnv,cwd=self.getPath()).stdout.read()              
        subprocess.Popen("vagrant up", shell=True, stdout=subprocess.PIPE,env=instanceEnv,cwd=self.getPath()).stdout.read()
        os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)        
        for root, dirs, files in os.walk(self.getPath()):  
            for d in dirs:  
                os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
            for f in files:
                os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)
  
    def destroy(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR        
        subprocess.Popen("vagrant destroy -f", shell=True, stdout=subprocess.PIPE,cwd=self.getPath()).stdout.read()
        shutil.rmtree(self.getPath())
              
    def stop(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        subprocess.Popen("vagrant halt", shell=True, stdout=subprocess.PIPE, env=instanceEnv,cwd=self.getPath()).stdout.read()              

    def ssh(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        val = subprocess.Popen("vagrant ssh", shell=True, env=instanceEnv, stderr=subprocess.PIPE, cwd=self.getPath())
        while True:
            out = val.stderr.read(1)
            if out == '' and val.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
                
    @classmethod
    def to_yaml(cls, dumper, data):           
        representation = {
                               "name" : data.name,
                               "template" : data.template,
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
    
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node,deep=True)   
        arch = None
        if "arch" in representation.keys() or representation["arch"] in (Architecture.__members__).keys():                
            arch = Architecture[representation["arch"]]
        
        provider = None
        if "provider" in representation.keys() or representation["provider"] in (Provider.__members__).keys():                
            provider = Provider[representation["provider"]]
        
        provisioner = None
        if "provisioner" in representation.keys() or representation["provisioner"] in (Provisioner.__members__).keys():                
            provisioner = Provisioner[representation["provisioner"]]
            
        name = os.path.basename(os.path.dirname(loader.stream.name))
        template = None       
        if "template" in representation.keys():                
            template = representation["template"]
            
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
