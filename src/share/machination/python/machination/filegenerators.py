import os
import yaml
import shutil
from abc import abstractmethod

from machination.exceptions import InvalidMachineTemplateException
from machination.exceptions import PathNotExistError,InvalidArgumentValue
from machination.constants import MACHINATION_INSTALLDIR, MACHINATION_USERDIR
from machination.constants import MACHINATION_BASEPROVISIONERSDIR, MACHINATION_USERPROVISIONERSDIR
import machination.core 


class ProvisionerFileGenerator:

    @abstractmethod
    def generateFiles(self):
        pass

class AnsibleProvisionerFileGenerator(ProvisionerFileGenerator):
    @staticmethod

    def generateFiles(template,dest):
        if type(template) is not  machination.core.MachineTemplate:
            raise InvalidArgumentValue("template")
        
        if not os.path.exists(dest):
            raise PathNotExistError(dest)
        playbookPath = None
        for d in [os.path.join(MACHINATION_BASEPROVISIONERSDIR,"ansible","playbooks"),os.path.join(MACHINATION_USERPROVISIONERSDIR,"ansible","playbooks")] :
            playbookPath = os.path.join(d,"{0}.playbook".format(template.getName()))
            if not os.path.exists(playbookPath):
                playbookPath = None
            else:
                break
                
        if playbookPath == None:
            raise InvalidMachineTemplateException(template.getName())
        else:
            openedFile = open(playbookPath)
            playbook = yaml.load(openedFile)
            for r in playbook[0]["roles"]:
                roleDirs = [os.path.join(MACHINATION_INSTALLDIR,"share","machination","provisioners","ansible","roles",r),os.path.join(MACHINATION_USERDIR,"provisioners","ansible","roles",r)]
                for roleDir in roleDirs:
                    if os.path.exists(roleDir):
                        shutil.copytree(roleDir, os.path.join(dest,"roles",r), True)
                        machination.helpers.mkdir_p(os.path.join(dest,"playbooks"))
                        shutil.copy(playbookPath, os.path.join(dest,"playbooks","{0}.playbook".format(template.getName())))
                        break
                    else:
                        raise PathNotExistError(roleDir)
            ansibleConfig=open(os.path.join(dest,"ansible.cfg"), "w+")
            ansibleConfig.write("[defaults]\r\n")
            ansibleConfig.write("roles_path = ./roles")
