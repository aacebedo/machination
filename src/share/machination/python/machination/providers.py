import subprocess
import re
from machination.helpers import accepts
from machination.exceptions import InvalidArgumentValue
from machination.loggers import PROVIDERSLOGGER

from abc import abstractmethod
 
class Provider(object):
    @abstractmethod
    def generateFileFor(self,instance):
      pass
    
    @staticmethod
    @accepts(str)
    def fromString(val):
      vals = {
                "docker" : DockerProvider,
                "vbox" : VBoxProvider,
                }
      if val in vals:
        return vals[val]
      else:
        raise InvalidArgumentValue("Unknown provider",val)
      
    @abstractmethod
    def __str__(self):
      pass
    
    @abstractmethod
    def needsProvision(self,instance):
      pass
    
class DockerProvider(Provider):
    @abstractmethod
    def generateFileFor(self,instance):
      folders = {}
      for f in instance.getSharedFolders():
        folders[f.getHostDir()] = f.getGuestDir()
      instance.getPackerFile()["variables"]["provider"] = self.__str__().lower()
      builder = {}
      builder["type"] = "docker"
      builder["image"] = "aacebedo/ubuntu-{{user `os_version`}}-vagrant-{{user `architecture`}}"
      builder["export_path"] = "machination-{{user `template_name`}}-{{user `architecture`}}-{{user `os_version`}}-{{user `provisioner`}}.tar"
      builder["run_command"] = ["-d","-i","-t", "--privileged","{{.Image}}","/sbin/init"]
      builder["volumes"] = folders
      instance.getPackerFile()["builders"].append(builder)
      
      postproc = {}
      postproc["type"] = "docker-import"
      postproc["repository"] = "machination-{{user `template_name`}}-{{user `architecture`}}-{{user `os_version`}}-{{user `provisioner`}}"
      postproc["tag"] = str(instance.getTemplate().getVersion())
      instance.getPackerFile()["post-processors"].append(postproc)
      PROVIDERSLOGGER.debug("Files generated for docker provider.")

    def __str__(self):
      return "docker"
    
    @abstractmethod
    def needsProvision(self,instance):
      imageName = "machination-{0}-{1}-{2}-{3}".format(instance.getTemplate().getName().lower(),
                                                           str(instance.getArch()).lower(),
                                                           instance.getOsVersion().lower(),
                                                           str(instance.getProvisioner()).lower())
      regex = ("(.*){0}( *){1}(.*)".format(imageName,str(instance.getTemplate().getVersion())))
      p = subprocess.Popen("docker images -a", shell=True, stderr=subprocess.PIPE,stdout=subprocess.PIPE)
      out = p.communicate()[0]
      if p.returncode == 0:
        return (re.search(regex,out) == None)
      else:
        raise RuntimeError("Internal error when processing provider of instance '{0}'".format(instance.getName()));
      
class VBoxProvider(Provider):
    @abstractmethod
    def generateFileFor(self,instance):
      folders = {}
      for f in instance.getSharedFolders():
        folders[f.getHostDir()] = f.getGuestDir()
      instance.getPackerFile()["variables"]["provider"] = self.__str__().lower()
      builder = {}
      builder["type"] = "virtualbox-iso"
      builder["guest_os_type"] = "Ubuntu_64"
      builder["iso_url"] = "http://releases.ubuntu.com/trusty/ubuntu-14.04.2-server-amd64.iso"
      builder["iso_checksum_type"] = "none"
      builder["ssh_username"] = "vagrant"
      builder["boot_command"] = [ "<esc><esc><enter><wait>",
                                  "/install/vmlinuz noapic ",
                                  "preseed/url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/preseed.cfg ",
                                  "debian-installer=en_US auto locale=en_US kbd-chooser/method=us ",
                                  "hostname={{ .Name }} ",
                                  "fb=false debconf/frontend=noninteractive ",
                                  "keyboard-configuration/modelcode=SKIP keyboard-configuration/layout=USA ",
                                  "keyboard-configuration/variant=USA console-setup/ask_detect=false ",
                                  "initrd=/install/initrd.gz -- <enter>"
      ]
      instance.getPackerFile()["builders"].append(builder)
      PROVIDERSLOGGER.debug("Files generated for Vbox provider.")

    def __str__(self):
      return "vbox"
    
    @abstractmethod
    def needsProvision(self,instance):
      # Vbox always needs provisioning
      return True