#
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
#
"""
This file contains the core classes of machination
"""

import re
import os
import yaml
import json
import subprocess
import sys
import shutil
import traceback
import hashlib

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

from machination.helpers import accepts, check_list_elements
from machination.loggers import CORELOGGER
from machination.helpers import generate_hash_of_file

class NetworkInterface(yaml.YAMLObject):
    """
    Class representing a network interface
    """
    yaml_tag = "!NetworkInterface"

    @accepts(None, str, str, str, None)
    def __init__(self, ipAddr, macAddr, hostname="None"):
        """
        Constructor
        """
        # Check each given argument
        # IP Address can be also dhcp
        if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}\
                    (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$", ipAddr):
            self.ip_addr = ipAddr
        else:
            raise InvalidArgumentValue("ipAddr", ipAddr)
        if re.match("^([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})$", macAddr):
            self.mac_addr = macAddr
        else:
            raise InvalidArgumentValue("macAddr", macAddr)

        if hostname is None or (isinstance(hostname, str) and
                                re.match("^([0-9a-zA-Z]*)$", hostname)):
            self.hostname = hostname
        else:
            raise InvalidArgumentValue("hostname", hostname)

    def get_ip_addr(self):
        """
        Returns the IP address of the interface
        """
        return self.ip_addr

    def get_mac_addr(self):
        """
        Returns the MAC address of the interface
        """
        return self.mac_addr

    def get_host_name(self):
        """
        Returns the hostname of the interface
        """
        if self.hostname is None:
            return ""
        else:
            return self.hostname

    def __str__(self):
        res = ""
        if self.hostname is not None:
            res = self.hostname + "|"
        return res + self.get_ip_addr() + "|" + self.get_mac_addr()

    @classmethod
    def to_yaml(cls, dumper, data):
        """
        Function to dump a network interface to yaml
        """
        representation = {
            "ip_addr": data.get_ip_addr(),
            "mac_addr": data.get_mac_addr(),
        }
        # Only dump the hostname if it has been set
        if data.get_host_name() != None:
            representation["hostname"] = data.get_host_name()
        return dumper.represent_mapping(data.yaml_tag, representation)

    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)
        # Need to check if IP Address or MAC Address are available
        if not "ip_addr" in representation.keys():
            raise InvalidYAMLException(
                "Invalid Network Interface: Missing IP address")

        if not "mac_addr" in representation.keys():
            raise InvalidYAMLException(
                "Invalid Network Interface: Missing MAC address")

        hostname = None
        if "hostname" in representation.keys():
            hostname = representation["hostname"]

        return NetworkInterface(representation["ip_addr"],
                                representation["mac_addr"], hostname)

class SharedFolder(yaml.YAMLObject):
    """
    Class representing a sync folder between host and guest
    """
    yaml_tag = "!SharedFolder"

    @accepts(None, str, str)
    def __init__(self, host_dir, guest_dir):
        """
        Constructor
        """
        # Path on the host must exist
        if os.path.exists(host_dir):
            self.host_dir = host_dir
        else:
            raise PathNotExistError(host_dir)
        if re.match("^(\/.*)$", guest_dir):
            self.guest_dir = guest_dir
        else:
            raise InvalidArgumentValue("guest_dir", guest_dir)

    def get_host_dir(self):
        """
        Returns the host directory
        """
        return self.host_dir

    def get_guest_dir(self):
        """
        Returns the guest directory
        """
        return self.guest_dir

    def __str__(self):
        return self.host_dir + " => " + self.guest_dir

    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
            "host_dir": data.get_host_dir(),
            "guest_dir": data.get_guest_dir()
        }
        return dumper.represent_mapping(data.yaml_tag, representation)

    #
    # Function to create a sharedfolder from yaml
    #
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)
        # A Shared folder shall have a host_dir and a guest_dir
        if not "host_dir" in representation.keys():
            raise InvalidYAMLException(
                "Invalid shared folder: missing host directory")

        if not "guest_dir" in representation.keys():
            raise InvalidYAMLException(
                "Invalid shared folder: missing guest directory")

        return SharedFolder(representation["host_dir"],
                            representation["guest_dir"])

class OperatingSystem(yaml.YAMLObject):
    """
    Class representing a base system
    """
    yaml_tag = "!OperatingSystem"

    @accepts(None, str, Architecture)
    def __init__(self, name, arch):
        """
        Constructor
        """
        self.name = name
        self.arch = arch
        
    def get_architecture(self):
        """
        Returns the architectures
        """
        return self.arch

    def get_name(self):
        """
        Returns the name directory
        """
        return self.name

    def __str__(self):
        return "{} ({})".format(self.name,self.get_architecture())

    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
            "name": data.get_name(),
            "arch": str(data.get_architecture())
        }
        return dumper.represent_mapping(data.yaml_tag, representation)

    #
    # Function to create a sharedfolder from yaml
    #
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)
        # A Shared folder shall have a host_dir and a guest_dir
        if not "name" in representation.keys():
            raise InvalidYAMLException(
                "Invalid base system: missing name")

        if not "arch" in representation.keys():
            raise InvalidYAMLException(
"Invalid base system: missing architecture")
            

        return OperatingSystem(representation["name"],Architecture.from_string(representation["arch"]))
        
class MachineTemplate(yaml.YAMLObject):
    """
    Class representing a machine template
    """
    yaml_tag = '!MachineTemplate'
    #
    # Constructor
    #
    @accepts(None, str, list, list, list, None, str, list)
    def __init__(self, path, operating_systems,
                 providers, provisioners, guest_interfaces, comments,
                 roles):
        # Checking the arguments

        if not os.path.exists(path):
            raise InvalidArgumentValue("Template path", path)

        if len(operating_systems) == 0 \
        or not check_list_elements(operating_systems, OperatingSystem):
            raise InvalidMachineTemplateException(
                "Invalid operating system")

        if len(providers) == 0 \
        or not check_list_elements(providers, Provider):
            raise InvalidMachineTemplateException(
                "Invalid number of providers")

        if len(provisioners) == 0 \
        or not check_list_elements(provisioners, Provisioner):
            raise InvalidMachineTemplateException(
                "Invalid number of provisioners")

        if len(roles) == 0 or not check_list_elements(roles, str):
            raise InvalidMachineTemplateException("Invalid number of roles")

        file_name = os.path.basename(path)
        self.name = os.path.splitext(file_name)[0]

        self.path = path
        self.operating_systems = operating_systems
        self.providers = providers
        self.provisioners = provisioners
        self.guest_interfaces = guest_interfaces
        self.roles = roles
        self.comments = comments

    def get_path(self):
        """
        Returns the path of the template
        """
        return self.path

    def get_operating_systems(self):
        """
        Returns the operating systems of the template
        """
        return self.operating_systems

    def get_providers(self):
        """
        Returns the providers of the template
        """
        return self.providers

    def get_provisioners(self):
        """
        Returns the provisioners of the template
        """
        return self.provisioners

    def get_guest_interfaces(self):
        """
        Returns the guest interfaces of the template
        """
        return self.guest_interfaces

    def get_name(self):
        """
        Returns the name of the template
        """
        return self.name

    def get_comments(self):
        """
        Returns the comments of the template
        """
        return self.comments

    def get_roles(self):
        """
        Returns the roles of the template
        """
        return self.roles

    def __str__(self):
        return self.get_name()

    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
            "path": data.get_path(),
            "operating_systems": data.get_operating_systems(),
            "providers": str(data.get_providers()),
            "provisioners": str(data.get_provisioners()),
            "guest_interfaces": data.get_guest_interfaces(),
            "comments": data.get_comments(),
            "roles": data.get_roles()
        }
        node = dumper.represent_mapping(data.yaml_tag, representation)
        return node

    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)
        # Check if architectures are present in the template
        operating_systems = []
        if "operating_systems" in representation.keys():
            operating_systems = representation["operating_systems"]

        providers = []
        # Check if providers are present in the template
        if "providers" in representation.keys() \
          and isinstance(representation["providers"], list):
            for provider in representation["providers"]:
                providers.append(Provider.from_string(provider)())

        provisioners = []
        # Check if provisioners are present in the template
        if "provisioners" in representation.keys() \
          and isinstance(representation["provisioners"], list):
            for provisioner in representation["provisioners"]:
                provisioners.append(Provisioner.from_string(provisioner)())
                
        guest_interfaces = 0
        if "guest_interfaces" in representation.keys():
            guest_interfaces = representation["guest_interfaces"]

        roles = []
        if "roles" in representation.keys():
            roles = representation["roles"]

        comments = ""
        if "comments" in representation.keys():
            comments = representation["comments"]

        return MachineTemplate(loader.stream.name,
                               operating_systems,
                               providers,
                               provisioners,
                               guest_interfaces,
                               comments,
                               roles)

class MachineInstance(yaml.YAMLObject):
    """
    Class representing a MachineInstance instance
    """
    yaml_tag = '!MachineInstance'
    #
    # Constructor
    #
    @accepts(None, str, MachineTemplate, OperatingSystem,
             Provider, Provisioner, list, str, list, None)
    def __init__(self, name, template, operating_system, provider,
                 provisioner, guest_interfaces, host_interface,
                 shared_folders, template_hash):
        # Check the arguments

        if len(name) == 0:
            raise InvalidArgumentValue("name", name)

        # Manually check the type of list elements
        for i in guest_interfaces:
            if not isinstance(i, NetworkInterface):
                raise InvalidArgumentValue("guest_interfaces", i)

        for folder in shared_folders:
            if not isinstance(folder, SharedFolder):
                raise InvalidArgumentValue("shared_folder", folder)
        self.name = name
        self.template = template
        self.operating_system = operating_system
        self.provider = provider
        self.provisioner = provisioner
        self.guest_interfaces = guest_interfaces
        self.shared_folders = shared_folders
        self.host_interface = host_interface
        self.packer_file = {}
        self.template_hash = template_hash

    def get_path(self):
        """
        Returns the path of the instance
        """
        return os.path.join(MACHINATION_USERINSTANCESDIR, self.get_name())

    def get_packer_file(self):
        """
        Returns the file of the instance
        """
        return self.packer_file

    def generate_files(self):
        """
        Generate the files for the instance
        """
        os.makedirs(self.get_path())

        # Generate the file related to the provisioner and the provider
        self.get_packer_file()["builders"] = []
        self.get_packer_file()["provisioners"] = []
        self.get_packer_file()["post-processors"] = []

        self.get_provider().generate_instance_files(self)
        self.get_provisioner().generate_instance_files(self)

        outfile = open(
            os.path.join(self.get_path(),
                         MACHINATION_PACKERFILE_NAME),
            "w")
        json.dump(self.get_packer_file(), outfile, indent=2)
        outfile.close()
        template_hash = hashlib.sha1()
        self.get_provisioner().generate_instance_hash(self, template_hash)
        generate_hash_of_file(
            os.path.join(self.get_path(), "Vagrantfile"),template_hash)
        self.template_hash = template_hash.hexdigest()
        # Create the machine config file
        config_file = yaml.dump(self)
        opened_file = open(
            os.path.join(self.get_path(),
                         MACHINATION_CONFIGFILE_NAME),
            "w+")
        opened_file.write(config_file)
        opened_file.close()

    def create(self):
        """
        Create the files of the instance
        """
        # If the machine does not exist yet
        if not os.path.exists(self.get_path()):
            try:
                self.generate_files()
                self.pack()
            except Exception as exception:
                # shutil.rmtree(self.get_path())
                CORELOGGER.debug(traceback.format_exc())
                raise exception
        else:
            # shutil.rmtree(self.get_path())
            # Raise an error about the fact the machine already exists
            raise RuntimeError("MachineInstance instance '{0}' already exists"\
                               .format(
                    self.get_path()))

    def pack(self):
        """
        Pack the instance using packer
        """
        # If the machine does not exist yet
        if os.path.exists(self.get_path()):
            if self.get_provider().needs_provisioning(self):
                CORELOGGER.debug(
                    "Image needs provisioning, starting packer...")

                # Fire up the vagrant machine
                cmd = ["packer","build",
                      "-var","provisioner={}".format(str(self.get_provisioner()).lower()),
                       "-var","provider={}".format(str(self.get_provider()).lower()),
                       "-var","operating_system_architecture={}".format(str(self.get_operating_system().get_architecture()).lower()),
                       "-var","operating_system_name={}".format(self.get_operating_system().get_name().lower()),
                       "-var","hash={}".format(self.get_template_hash()),
                      os.path.join(".", MACHINATION_PACKERFILE_NAME)]
                CORELOGGER.info("executed command {}".format(cmd))
                process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    cwd=self.get_path())
                process.communicate()
                return_code = process.returncode
                if return_code != 0:
                    raise RuntimeError(
                        "Error while creating packing \
                        '{}'".format(self.get_name()))
        else:
            raise RuntimeError(
                "Error while packing machine \
                '{}'".format(self.get_name()))
    #
    # Simple getters
    #

    def get_name(self):
        return self.name

    def get_template_hash(self):
        return self.template_hash

    def get_provisioner(self):
        return self.provisioner

    def get_provider(self):
        return self.provider

    def get_shared_folders(self):
        return self.shared_folders

    def get_template(self):
        return self.template

    def get_guest_interfaces(self):
        return self.guest_interfaces

    def get_operating_system(self):
        return self.operating_system

    def get_host_interface(self):
        return self.host_interface

    def get_image_name(self):
        return "machination-{0}-{1}-{2}-{3}".format(
            self.get_template().get_name().lower(),
            str(self.get_operating_system().get_architecture()).lower(),
            self.get_operating_system().get_name().lower(),
            str(self.get_provisioner()).lower())

    def __str__(self):
        return self.get_name()

    def start(self):
        """
        Function to start an instance
        This function must be ran as root as some action
        in the the provisioner or the provider may require a root access
        """
        # Fire up the vagrant machine
        self.pack()
        process = subprocess.Popen(
            ["vagrant","up","--provider={0}".format(str(self.get_provider()))],
            stderr=subprocess.PIPE,
            cwd=self.get_path())
        err = process.communicate()[0]
        if process.returncode != 0:
            CORELOGGER.critical(err)
            raise RuntimeError(
                "Error while starting machine instance: \
                '{}'".format(self.get_name()))

    #
    # Function to destroy an instance
    #
    def destroy(self):
        # Destroy the vagrant machine
        process = subprocess.Popen(
            ["vagrant","destroy","-f"],
            stdout=subprocess.PIPE,
            cwd=self.get_path())
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(
                "Error while destroying machine instance \
                '{}'".format(self.get_name()))
        shutil.rmtree(self.get_path())

    #
    # Function to stop an instance
    #
    def stop(self):
        process = subprocess.Popen(
            ["vagrant","halt"],
            stderr=subprocess.PIPE,
            cwd=self.get_path())
        process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                "Error while stopping machine instance: \
                '{}'".format(self.get_name()))

    #
    #
    def get_infos_at_runtime(self):
        res = []
        ip_addr_search_group = None
        is_started = self.is_started()
        if is_started:
            process = subprocess.Popen(
                ["vagrant","ssh-config"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                cwd=self.get_path())
            out = process.communicate()[0]
            if process.returncode == 0:
                ip_addr_search_group = re.search("HostName (.*)", out.decode())

        if ip_addr_search_group is None:
            ip_addr_search = "N/A"
        else:
            ip_addr_search = ip_addr_search_group.group(1)
        i = 0
        res.append({"name" : "eth{}".format(i),
                 "ip" : ip_addr_search,
                 "mac" : "N/A",
                 "host_interface" : "N/A",
                 "hostname" : "N/A",
                 })
        i += 1
        if len(self.get_guest_interfaces()) != 0:
            for intf in self.get_guest_interfaces():
                res.add({"name" : "eth{}".format(i),
                         "ip" : intf.get_ip_addr(),
                         "mac" : intf.get_mac_addr(),
                         "host_interface": intf.get_host_interface(),
                         "hostname": intf.get_host_name() if intf.get_host_name() != None and intf.get_host_name() != "" else "N/A"
                         })
                i += 1
        return res
    #
    # Function to ssh to an instance
    #
    def ssh(self, command=None):
        if self.is_started():
            # Start vagrant ssh to ssh into the instance
            if command is None:
                val = subprocess.Popen(
                    ["vagrant","ssh"],
                    stderr=subprocess.PIPE,
                    cwd=self.get_path())
            else:
                val = subprocess.Popen(
                    ["vagrant","ssh", "-c \"{0}\"".format(command)],
                    stderr=subprocess.PIPE,
                    cwd=self.get_path())
            # get the output of the machine
            while True:
                out = val.stderr.read(1)
                if out.decode() == '' and val.poll() != None:
                    break
                if out.decode() != '':
                    sys.stdout.write(out.decode())
                    sys.stdout.flush()
        else:
            raise RuntimeError("Machine instance not started")

    def is_started(self):
        process = subprocess.Popen(
            ["vagrant","status"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=self.get_path())
        
        out = process.communicate()[0]
        is_started = re.search("default[ \t]+running.*",
                                     out.decode()) != None
        if process.returncode == 0 and is_started:
            return True
        else:
            return False

    #
    # Function to dump the object to YAML
    #
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
            "template":
            "{0}|{1}".format(data.get_template().get_name(),
                             data.get_template_hash()),
            "operating_system": data.get_operating_system(),
            "provider": str(data.get_provider()),
            "provisioner": str(data.get_provisioner()),
            "guest_interfaces": data.get_guest_interfaces(),
            "host_interface": data.get_host_interface(),
            "shared_folders": data.get_shared_folders()
        }
        node = dumper.represent_mapping(data.yaml_tag, representation)
        return node

    #
    # Function to create an object from YAML
    #
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)

        provider = None
        if "provider" in representation.keys():
            provider = Provider.from_string(representation["provider"])()

        provisioner = None
        if "provisioner" in representation.keys():
            provisioner = Provisioner.from_string(
                representation["provisioner"])()

        name = os.path.basename(os.path.dirname(loader.stream.name))

        template = None
        template_hash = None
        if "template" in representation.keys():
            template_name, template_hash = representation["template"].split("|")
            template = MACHINE_TEMPLATE_REGISTRY.get_templates()[template_name]

        operating_system = None
        if "operating_system" in representation.keys():
            operating_system = representation["operating_system"]

        guest_interfaces = []
        if "guest_interfaces" in representation.keys():
            guest_interfaces = representation["guest_interfaces"]

        shared_folders = []
        if "shared_folders" in representation.keys():
            shared_folders = representation["shared_folders"]

        host_interface = None
        if "host_interface" in representation.keys():
            host_interface = representation["host_interface"]

        return MachineInstance(name,
                               template,
                               operating_system,
                               provider,
                               provisioner,
                               guest_interfaces,
                               host_interface,
                               shared_folders,
                               template_hash)
