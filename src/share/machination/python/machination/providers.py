import subprocess
import re
import requests
import StringIO
import shutil
import os
from machination.helpers import accepts
from machination.exceptions import InvalidArgumentValue
from machination.loggers import PROVIDERSLOGGER
from machination.constants import MACHINATION_VBOXDIR
from abc import abstractmethod
 
class Provider(object):
    @abstractmethod
    def generateFilesFor(self,instance):
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
    def generateFilesFor(self,instance):
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
    def generateFilesFor(self,instance):
      req = requests.get("http://releases.ubuntu.com/{0}/MD5SUMS".format(instance.getOsVersion()))
      md5file = StringIO.StringIO(req.content) 
  
      versionLine = ""
      for line in md5file:
        if "server-amd64" in line:
          versionLine = line.rstrip('\n\r ')
          break
      splittedVersionLine = versionLine.split('*')
      if (len(splittedVersionLine) != 2):
        raise RuntimeError("Unable to find OS version {0} in checksum file of ubuntu".format(instance.getOsVersion()))
      
      shutil.copy2(os.path.join(MACHINATION_VBOXDIR,"preseed.cfg"),os.path.join(instance.getPath(),"preseed.cfg"))        
      folders = {}
      for f in instance.getSharedFolders():
        folders[f.getHostDir()] = f.getGuestDir()
      instance.getPackerFile()["variables"]["provider"] = self.__str__().lower()
      builder = {}
      builder["type"] = "virtualbox-iso"
      builder["guest_os_type"] = "Ubuntu_64"
      builder["iso_url"] = "http://releases.ubuntu.com/trusty/ubuntu-14.04.2-server-amd64.iso"
      builder["iso_checksum_type"] = "md5"
      builder["iso_checksum"] = splittedVersionLine[0].rstrip(" ")
      builder["http_directory"] = "./"
      builder["iso_checksum_type"] = "none"
      builder["http_port_max"] = "9500"
      builder["ssh_username"] = "vagrant"
      builder["ssh_password"] = "vagrant"
      builder["ssh_wait_timeout"] = "20m"
      builder["headless"] = "true"
      builder["guest_additions_mode"] = "disable"
      builder["shutdown_command"] = "sudo -S shutdown -P now"
      builder["boot_command"] = [ "<esc><esc><enter><wait>",
                                  "/install/vmlinuz noapic ",
                                  "preseed/url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/preseed.cfg ",
                                  "debian-installer=en_US auto locale=en_US kbd-chooser/method=us ",
                                  "hostname={{user `hostname`}} ",
                                  "fb=false debconf/frontend=noninteractive ",
                                  "keyboard-configuration/modelcode=SKIP keyboard-configuration/layout=USA ",
                                  "keyboard-configuration/variant=USA console-setup/ask_detect=false ",
                                  "initrd=/install/initrd.gz -- <enter>"
      ]        
      instance.getPackerFile()["builders"].append(builder)
      
      postproc = {}   
      postproc["type"] = "vagrant"
      postproc["output"] = "machination-{0}-{1}-{2}-{3}.box".format(instance.getTemplate().getName().lower(),
                                                                    str(instance.getArchitecture()).lower(),
                                                                    instance.getOsVersion().lower(),
                                                                    str(instance.getProvisioner()).lower())
      postproc["compression_level"] = 0
      
      instance.getPackerFile()["post-processors"].append(postproc)
    
      PROVIDERSLOGGER.debug("Files generated for Vbox provider.")

    def __str__(self):
      return "vbox"
    
    @abstractmethod
    def needsProvision(self,instance):
      # Vbox always needs provisioning
      imageName = "machination-{0}-{1}-{2}-{3}".format(instance.getTemplate().getName().lower(),
                                                           str(instance.getArchitecture()).lower(),
                                                           instance.getOsVersion().lower(),
                                                           str(instance.getProvisioner()).lower())
      regex = "(.*){0}(.*)".format(imageName)
      p = subprocess.Popen("vagrant box list", shell=True, stderr=subprocess.PIPE,stdout=subprocess.PIPE)
      out = p.communicate()[0]
      if p.returncode == 0:
        return (re.search(regex,out) == None)
      else:
        raise RuntimeError("Internal error when processing provider of instance '{0}'".format(instance.getName()));