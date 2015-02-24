import os
import yaml
import shutil
from abc import abstractmethod

from machination.exceptions import PathNotExistError
from machination.constants import MACHINATION_INSTALLDIR, MACHINATION_USERDIR


class ProvisionerFileGenerator:
    
    @abstractmethod
    def generateFiles(self):
        pass
    
class AnsibleProvisionerFileGenerator(ProvisionerFileGenerator):    
    def generateFiles(self,playbookPath,dest):
        
        if not os.path.exists(dest):
            raise PathNotExistError(dest)       
        
        if not os.path.exists(playbookPath):
            raise PathNotExistError(playbookPath)
        else:
            openedFile = open(playbookPath)
            playbook = yaml.load(openedFile)
            dstDir = os.path.join(dest,"roles")
            for r in playbook[0]["roles"]:
                roleDirs = [os.path.join(MACHINATION_INSTALLDIR,"share","machination","provisioners","ansible","roles",r),os.path.join(MACHINATION_USERDIR,"provisioners","ansible","roles",r)]
                for roleDir in roleDirs:
                    if os.path.exists(roleDir):
                        shutil.copytree(roleDir, os.path.join(dstDir,r), True)
                        break
                    else:
                        raise PathNotExistError(roleDir)
        