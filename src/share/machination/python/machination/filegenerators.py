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

import os
import yaml
import shutil
from abc import abstractmethod

from machination.exceptions import InvalidMachineTemplateException
from machination.exceptions import PathNotExistError,InvalidArgumentValue
from machination.constants import MACHINATION_USERANSIBLEPLAYBOOKSDIR, MACHINATION_DEFAULTANSIBLEPLAYBOOKSDIR, MACHINATION_DEFAULTANSIBLEROLESDIR, MACHINATION_USERANSIBLEROLESDIR
from machination.loggers import FILEGENERATORLOGGER
import machination.core


class ProvisionerFileGenerator:
    @abstractmethod
    def generateFiles(self):
        pass

class AnsibleProvisionerFileGenerator(ProvisionerFileGenerator):
    @staticmethod
    def copyRole(dest,role):
      roleDir = None
      roleDirs = [os.path.join(MACHINATION_DEFAULTANSIBLEROLESDIR,role),os.path.join(MACHINATION_USERANSIBLEROLESDIR,role)]

      for tmpRoleDir in roleDirs:
        if os.path.exists(tmpRoleDir):
          roleDir = tmpRoleDir
          break
        else:
          roleDir = None

      if roleDir != None and os.path.exists(roleDir):
        shutil.copytree(roleDir, os.path.join(dest,"roles",role), True)
        metaPath = os.path.join(roleDir,"meta","main.yml")
        if os.path.exists(metaPath):
          openedFile = open(metaPath)
          metas = yaml.load(openedFile)
          if "dependencies" in metas.keys():
            for r in metas["dependencies"]:
              if "role" in r.keys() and not os.path.exists(os.path.join(dest,"roles",r["role"])):
                AnsibleProvisionerFileGenerator.copyRole(dest,r["role"])
      else:
        raise InvalidMachineTemplateException("Unable to find ansible role '{0}'.".format(role))

    @staticmethod
    def generateFiles(template,dest):
        if type(template) is not  machination.core.MachineTemplate:
            raise InvalidArgumentValue("template")
        if not os.path.exists(dest):
            raise PathNotExistError(dest)
        ansibleFilesDest = os.path.join(dest,"provisioners","ansible")
        playbookPath = None
        for d in [MACHINATION_DEFAULTANSIBLEPLAYBOOKSDIR,MACHINATION_USERANSIBLEPLAYBOOKSDIR] :
            playbookPath = os.path.join(d,"{0}.playbook".format(template.getName()))
            FILEGENERATORLOGGER.debug("Searching ansible playbook in '{0}'...".format(playbookPath))
            if not os.path.exists(playbookPath):
                playbookPath = None
            else:
                break
        if playbookPath == None:
            raise InvalidMachineTemplateException("Template '{0}' was not found".format(template.getName()))
        else:
            openedFile = open(playbookPath)
            playbook = yaml.load(openedFile)
            for r in playbook[0]["roles"]:
                AnsibleProvisionerFileGenerator.copyRole(ansibleFilesDest,r)
            machination.helpers.mkdir_p(os.path.join(ansibleFilesDest,"playbooks"))
            shutil.copy(playbookPath, os.path.join(ansibleFilesDest,"playbooks","{0}.playbook".format(template.getName())))
            ansibleConfig=open(os.path.join(dest,"ansible.cfg"), "w+")
            ansibleConfig.write("[defaults]\r\n")
            ansibleConfig.write("roles_path = {0}".format(os.path.join("provisioners","ansible","roles")))

