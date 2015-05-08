import shutil
import yaml
import os

from machination.helpers import accepts
from machination.exceptions import InvalidArgumentValue
from machination.exceptions import PathNotExistError
from machination.exceptions import InvalidMachineTemplateException
 
from machination.constants import MACHINATION_DEFAULTANSIBLEROLESDIR
from machination.constants import MACHINATION_USERANSIBLEROLESDIR
from machination.constants import MACHINATION_DEFAULTANSIBLEPLAYBOOKSDIR
from machination.constants import MACHINATION_USERANSIBLEPLAYBOOKSDIR

from machination.loggers import FILEGENERATORLOGGER

from machination.helpers import mkdir_p

from abc import abstractmethod

class Provisioner(object):
    @abstractmethod
    def generateFilesFor(self,instance):
      pass
    
    @staticmethod
    @accepts(str)
    def fromString(val):
      vals = {
                "ansible" : AnsibleProvisioner,
                }
      if val in vals:
        return vals[val]
      else:
        raise InvalidArgumentValue("Unknown provisioner")

    @abstractmethod
    def __str__(self):
      pass
      
class AnsibleProvisioner(Provisioner):
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
                AnsibleProvisioner.copyRole(dest,r["role"])
      else:
        raise InvalidMachineTemplateException("Unable to find ansible role '{0}'.".format(role))

    @abstractmethod
    def generateFilesFor(self,instance):
      if not os.path.exists(instance.getPath()):
          raise PathNotExistError(instance.getPath())
      ansibleFilesDest = os.path.join(instance.getPath(),"provisioners","ansible")
      mkdir_p(os.path.join(ansibleFilesDest))
      playbookPath = os.path.join(instance.getPath(),"provisioners","ansible","machine.playbook")
      playbook = [{}]
      playbook[0]["hosts"] = "all"
      playbook[0]["roles"] = instance.getTemplate().getRoles()
      playbookFile = open(playbookPath,'w')
      playbookFile.write(yaml.dump(playbook,default_flow_style=False))
    
      for r in playbook[0]["roles"]:
          AnsibleProvisioner.copyRole(ansibleFilesDest,r)
      instance.getPackerFile()["variables"]["provisioner"] = self.__str__().lower()
      instance.getPackerFile()["variables"]["ansible_staging_directory"] = "/tmp/packer-provisioner-ansible-local"
      
      provisioner = {}
      provisioner["type"] = "shell"
      provisioner["inline"] = ["apt-get install -y ansible python-apt"]
      instance.getPackerFile()["provisioners"].append(provisioner)
      
      provisioner = {}
      provisioner["type"] = "shell"
      provisioner["inline"] = ["mkdir -p {{ user `ansible_staging_directory` }}"]
      instance.getPackerFile()["provisioners"].append(provisioner)
      
      provisioner = {}
      provisioner["type"] = "file"
      provisioner["source"] = "provisioners/ansible/roles"
      provisioner["destination"] = "{{ user `ansible_staging_directory` }}"
      instance.getPackerFile()["provisioners"].append(provisioner)
      
      provisioner = {}
      provisioner["type"] = "ansible-local"
      provisioner["playbook_file"] = "provisioners/ansible/machine.playbook"
      instance.getPackerFile()["provisioners"].append(provisioner)
      
      provisioner = {}
      provisioner["type"] = "shell"
      provisioner["inline"] =  [ "rm -rf  {{ user `ansible_staging_directory` }}"]
      instance.getPackerFile()["provisioners"].append(provisioner)
      
      provisioner = {}
      provisioner["type"] = "shell"
      provisioner["inline"] = ["apt-get remove -y ansible && apt-get autoremove -y"]
      instance.getPackerFile()["provisioners"].append(provisioner)
      
       
    def __str__(self):
      return "ansible"
