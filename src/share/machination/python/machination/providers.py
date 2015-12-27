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
import hashlib
"""
This file contains the providers definition of machination
"""
import subprocess
import re
import requests
import shutil
import os
from io import StringIO
from machination.helpers import generate_hash_of_file
from machination.helpers import accepts
from machination.exceptions import InvalidArgumentValue
from machination.loggers import PROVIDERSLOGGER
from machination.constants import MACHINATION_VBOXDIR, MACHINATION_INSTALLDIR
from abc import abstractmethod

class Provider(object):
    """
    Base class for providers
    Children classes will be in charge on generating hashes and specific files
    for its implementation
    """
    @abstractmethod
    def generate_instance_files(self, instance):
        """
        Generate files for the given instance
        """
        raise NotImplementedError("Abstract method is not implemented")

    @abstractmethod
    def generate_instance_hash(self, instance, hash_value):
        """
        Generate hash for the given instance
        """
        raise NotImplementedError("Abstract method is not implemented")

    @staticmethod
    @accepts(str)
    def from_string(val):
        """
        Convert a string into a provider
        """
        vals = {
            "docker": DockerProvider,
            "virtualbox": VBoxProvider,
        }
        if val in vals:
            return vals[val]
        else:
            raise InvalidArgumentValue("Unknown provider", val)

    @abstractmethod
    def needs_provisioning(self, instance):
        """
        Returns true if the instance needs to be provisioned
        false otherwise
        """
        raise NotImplementedError("Abstract method is not implemented")


class DockerProvider(Provider):
    """
    Provider based on Docker
    """
    def generate_instance_files(self, instance):
        folders = {}
        for file_to_process in instance.get_shared_folders():
            folders[file_to_process.get_host_dir()] = \
            file_to_process.get_guest_dir()

        builder = {}
        builder["type"] = "docker"
        builder["image"] = "aacebedo/ubuntu-{{user `operating_system_name`}}-vagrant-\
{{user `operating_system_architecture`}}"
        builder["export_path"] = "./machine.box"
        builder[
            "run_command"] = [
                "-d",
                "-i",
                "-t",
                "--privileged",
                "{{.Image}}",
                "/sbin/init"]
        builder["volumes"] = folders
        instance.get_packer_file()["builders"].append(builder)

        postproc = {}
        postproc["type"] = "docker-import"
        postproc["repository"] = instance.get_image_name()
        postproc["tag"] = "{{user `hash`}}"
        instance.get_packer_file()["post-processors"].append(postproc)

        shutil.copy(
            os.path.join(MACHINATION_INSTALLDIR,
                         "share",
                         "machination",
                         "vagrant",
                         "Vagrantfile_docker"),
            os.path.join(instance.get_path(),
                         "Vagrantfile"))
        PROVIDERSLOGGER.debug("Files generated for docker provider.")

    def __str__(self):
        return "docker"
      
    def generate_instance_hash(self, instance, hash_value):
        pass

    def needs_provisioning(self, instance):
        regex = "(.*){0}( *){1}(.*)".format(
            instance.get_image_name(),
            str(instance.get_template_hash()))
        process = subprocess.Popen(
            ["docker","images", "-a"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        out = process.communicate()[0]
        if process.returncode == 0:
            return re.search(regex, out.decode()) == None
        else:
            raise RuntimeError(
                "Internal error when processing provider \
                of instance '{}'".format(instance.get_name()))


class VBoxProvider(Provider):
    """
    Provider supporting VirtualBox
    """
    def generate_instance_files(self, instance):
        req = requests.get(
            "http://releases.ubuntu.com/{}/MD5SUMS"
            .format(instance.get_operating_system().get_name()))
        md5file = StringIO.StringIO(req.content)

        version_line = ""
        for line in md5file:
            if "server-{0}".format(instance.get_operating_system().get_architecture()) in line:
                version_line = line.rstrip('\n\r ')
                break
        splitted_version_line = version_line.split('*')
        if len(splitted_version_line) != 2:
            raise RuntimeError(
                "Unable to find OS version {} \
                in checksum file of ubuntu".format(instance.get_operating_system().get_name()))

        shutil.copy2(
            os.path.join(MACHINATION_VBOXDIR,
                         "preseed.cfg"),
            os.path.join(instance.get_path(),
                         "preseed.cfg"))

        folders = {}
        for file in instance.get_shared_folders():
            folders[file.get_host_dir()] = file.get_guest_dir()

        builder = {}
        builder["type"] = "virtualbox-iso"
        builder["guest_os_type"] = "Linux_64"
        builder["iso_url"] = "http://releases.ubuntu.com/{0}/{1}".format(
            instance.get_operating_system().get_name(), splitted_version_line[1])
        builder["iso_checksum_type"] = "md5"
        builder["iso_checksum"] = splitted_version_line[0].rstrip(" ")
        builder["http_directory"] = "./"
        builder["http_port_min"] = "9000"
        builder["http_port_max"] = "9500"
        builder["ssh_username"] = "vagrant"
        builder["ssh_password"] = "vagrant"
        builder["ssh_wait_timeout"] = "20m"
        builder["headless"] = "true"
        builder["guest_additions_mode"] = "disable"
        builder[
            "shutdown_command"] = "echo 'vagrant' | sudo -E -S shutdown -P now"
        builder["boot_command"] = ["<esc><esc><enter><wait>",
                                   "/install/vmlinuz noapic ",
                                   "preseed/url=http://{{ .HTTPIP }}:\
                                   {{ .HTTPPort }}/preseed.cfg ",
                                   "debian-installer=en_US auto \
                                   locale=en_US kbd-chooser/method=us ",
                                   "hostname={0} ".format(instance.get_name()),
                                   "fb=false debconf/frontend=noninteractive ",
                                   "keyboard-configuration/modelcode=SKIP \
                                   keyboard-configuration/layout=FR ",
                                   "keyboard-configuration/variant=USA \
                                   console-setup/ask_detect=false ",
                                   "initrd=/install/initrd.gz -- <enter>"
                                  ]
        instance.get_packer_file()["builders"].append(builder)

        postproc = {}
        postproc["type"] = "vagrant-import"
        postproc["import_name"] = instance.get_image_name() + "-{{user `hash`}}"
        instance.get_packer_file()["post-processors"].append(postproc)

        shutil.copy(
            os.path.join(MACHINATION_INSTALLDIR,
                         "share",
                         "machination",
                         "vagrant",
                         "Vagrantfile_virtualbox"),
            os.path.join(instance.get_path(),
                         "Vagrantfile"))

        PROVIDERSLOGGER.debug("Files generated for virtualbox provider.")

    def __str__(self):
        return "virtualbox"

    def needs_provisioning(self, instance):
        # virtualbox always needs provisioning
        regex = "{0}-{1}(.*)".format(
            instance.get_image_name(),
            instance.get_template_hash())
        process = subprocess.Popen(
            ["vagrant","box","list"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        out = process.communicate()[0]
        if process.returncode == 0:
            return re.search(regex, out) == None
        else:
            raise RuntimeError(
                "Internal error when processing provider \
                of instance '{0}'".format(instance.get_name()))

    def generate_instance_hash(self, instance, hash_value):
        generate_hash_of_file(
            os.path.join(instance.get_path(),
                         "preseed.cfg"),
            hash_value)
