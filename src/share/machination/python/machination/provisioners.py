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
This file contains the provisioners definition of machination
"""
import yaml
import shutil
import os

from machination.helpers import accepts
from machination.helpers import generate_hash_of_dir
from machination.exceptions import InvalidArgumentValue
from machination.exceptions import PathNotExistError
from machination.exceptions import InvalidMachineTemplateException

from machination.constants import MACHINATION_DEFAULTANSIBLEROLESDIR
from machination.constants import MACHINATION_USERANSIBLEROLESDIR

from abc import abstractmethod

#pylint: disable=R0922
class Provisioner(object):
    """
    Base class for all provisioners
    """

    @abstractmethod
    def generate_instance_files(self, instance):
        """
        Generates files for the given instance
        """
        pass

    @abstractmethod
    def generate_instance_hash(self, instance):
        """
        Generates hash for the given instance
        """
        pass

    @staticmethod
    @accepts(str)
    def from_string(val):
        """
        Convert a string into a provisioner
        """
        vals = {
            "ansible": AnsibleProvisioner,
        }
        if val in vals:
            return vals[val]
        else:
            raise InvalidArgumentValue("Unknown provisioner")


class AnsibleProvisioner(Provisioner):
    """
    Provisioner with ansible support
    """
    @staticmethod
    def copy_role(dest, role):
        """
        Copy an ansible role into the instance directory
        """
        role_dir = None
        role_dirs = [
            os.path.join(
                MACHINATION_DEFAULTANSIBLEROLESDIR,
                role),
            os.path.join(
                MACHINATION_USERANSIBLEROLESDIR,
                role)]

        for tmp_role_dir in role_dirs:
            if os.path.exists(tmp_role_dir):
                role_dir = tmp_role_dir
                break
            else:
                role_dir = None

        if role_dir is not None and os.path.exists(role_dir):
            shutil.copytree(role_dir, os.path.join(dest, "roles", role), True)
            meta_path = os.path.join(role_dir, "meta", "main.yml")
            if os.path.exists(meta_path):
                opened_file = open(meta_path)
                metas = yaml.load(opened_file)
                if "dependencies" in metas.keys():
                    for dependency in metas["dependencies"]:
                        if "role" in dependency.keys() \
                          and not os.path.exists(
                                  os.path.join(dest, "roles",
                                               dependency["role"])):
                            AnsibleProvisioner.copy_role(dest,
                                                         dependency["role"])
        else:
            raise InvalidMachineTemplateException(
                "Unable to find ansible role '{0}'.".format(role))

    def generate_instance_hash(self, instance):
        res = None
        generate_hash_of_dir(
            os.path.join(instance.getPath(),
                         "provisioners",
                         "ansible"),
            res)
        return res

    def generate_instance_files(self, instance):
        if not os.path.exists(instance.getPath()):
            raise PathNotExistError(instance.getPath())
        ansible_files_dest = os.path.join(
            instance.getPath(),
            "provisioners",
            "ansible")
        os.makedirs(ansible_files_dest, exist_ok=True)
        playbook_path = os.path.join(
            instance.getPath(),
            "provisioners",
            "ansible",
            "machine.playbook")
        playbook = [{}]
        playbook[0]["hosts"] = "all"
        playbook[0]["roles"] = instance.getTemplate().getRoles()
        playbook_file = open(playbook_path, 'w')
        playbook_file.write(yaml.dump(playbook, default_flow_style=False))

        for role in playbook[0]["roles"]:
            AnsibleProvisioner.copy_role(ansible_files_dest, role)

        provisioner = {}
        provisioner["type"] = "shell"
        provisioner[
            "inline"] = ["apt-get install -y python-apt python-\
                          software-properties software-properties-common",
                         "add-apt-repository ppa:ansible/ansible -y",
                         "apt-get update",
                         "apt-get install -y ansible"]
        provisioner[
            "execute_command"] = "echo 'vagrant' | sudo -E -S sh '{{ .Path }}'"
        instance.getPackerFile()["provisioners"].append(provisioner)

        provisioner = {}
        provisioner["type"] = "shell"
        provisioner["inline"] = [
            "mkdir -p /tmp/packer-provisioner-ansible-local"]
        instance.getPackerFile()["provisioners"].append(provisioner)

        provisioner = {}
        provisioner["type"] = "file"
        provisioner["source"] = "provisioners/ansible/roles"
        provisioner["destination"] = "/tmp/packer-provisioner-ansible-local"
        instance.getPackerFile()["provisioners"].append(provisioner)

        provisioner = {}
        provisioner["type"] = "ansible-local"
        provisioner["playbook_file"] = "provisioners/ansible/machine.playbook"
        provisioner["command"] = "echo 'vagrant' | sudo -E -S ansible-playbook"

        instance.getPackerFile()["provisioners"].append(provisioner)

        provisioner = {}
        provisioner["type"] = "shell"
        provisioner["inline"] = [
            "rm -rf /tmp/packer-provisioner-ansible-local"]
        instance.getPackerFile()["provisioners"].append(provisioner)

        provisioner = {}
        provisioner["type"] = "shell"
        provisioner["inline"] = [
            "apt-get remove -y ansible && apt-get autoremove -y"]
        provisioner[
            "execute_command"] = "echo 'vagrant' | sudo -E -S sh '{{ .Path }}'"
        instance.getPackerFile()["provisioners"].append(provisioner)

    def __str__(self):
        return "ansible"
