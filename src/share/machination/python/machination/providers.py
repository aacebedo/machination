import subprocess
import re
import requests
import StringIO
import shutil
import os
from machination.helpers import generate_hash_of_file
from machination.helpers import accepts
from machination.exceptions import InvalidArgumentValue
from machination.loggers import PROVIDERSLOGGER
from machination.constants import MACHINATION_VBOXDIR, MACHINATION_INSTALLDIR
from abc import abstractmethod
 
class Provider(object):
    @abstractmethod
    def generateFilesFor(self, instance):
      pass

    @abstractmethod
    def generateHashFor(self, instance, hashValue):
      pass
    
    @staticmethod
    @accepts(str)
    def from_string(val):
      vals = {
                "docker" : DockerProvider,
                "virtualbox" : VBoxProvider,
                }
      if val in vals:
        return vals[val]
      else:
        raise InvalidArgumentValue("Unknown provider", val)
      
    @abstractmethod
    def __str__(self):
      pass
    
    @abstractmethod
    def needsProvisioning(self, instance):
      pass
    
class DockerProvider(Provider):
    @abstractmethod
    def generateFilesFor(self, instance):
      folders = {}
      for f in instance.getSharedFolders():
        folders[f.getHostDir()] = f.getGuestDir()
      
      builder = {}
      builder["type"] = "docker"
      builder["image"] = "aacebedo/ubuntu-{{user `osversion`}}-vagrant-{{user `architecture`}}"
      builder["export_path"] = "./machine.box"
      builder["run_command"] = ["-d", "-i" , "-t", "--privileged", "{{.Image}}", "/sbin/init"]
      builder["volumes"] = folders
      instance.getPackerFile()["builders"].append(builder) 
      
      postproc = {}
      postproc["type"] = "docker-import"
      postproc["repository"] = instance.getImageName()
      postproc["tag"] = "{{user `hash`}}"
      instance.getPackerFile()["post-processors"].append(postproc)
      
      shutil.copy(os.path.join(MACHINATION_INSTALLDIR, "share", "machination", "vagrant", "Vagrantfile_docker"), os.path.join(instance.getPath(), "Vagrantfile"))
      PROVIDERSLOGGER.debug("Files generated for docker provider.")

    def __str__(self):
      return "docker"
    
    @abstractmethod
    def generateHashFor(self, instance, hashValue):
      pass
    
    @abstractmethod
    def needsProvisioning(self, instance):
      regex = "(.*){0}( *){1}(.*)".format(instance.getImageName(), str(instance.getTemplateHash()))
      print(regex)
      p = subprocess.Popen("docker images -a", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
      out = p.communicate()[0]
      if p.returncode == 0:
        return (re.search(regex, out) == None)
      else:
        raise RuntimeError("Internal error when processing provider of instance '{0}'".format(instance.getName()));
      
class VBoxProvider(Provider):
    @abstractmethod
    def generateFilesFor(self, instance):
      req = requests.get("http://releases.ubuntu.com/{0}/MD5SUMS".format(instance.getOsVersion()))
      md5file = StringIO.StringIO(req.content) 
  
      versionLine = ""
      for line in md5file:
        if "server-{0}".format(instance.getArchitecture()) in line:
          versionLine = line.rstrip('\n\r ')
          break
      splittedVersionLine = versionLine.split('*')
      if (len(splittedVersionLine) != 2):
        raise RuntimeError("Unable to find OS version {0} in checksum file of ubuntu".format(instance.getOsVersion()))
      
      shutil.copy2(os.path.join(MACHINATION_VBOXDIR, "preseed.cfg"), os.path.join(instance.getPath(), "preseed.cfg"))
      
      folders = {}
      for f in instance.getSharedFolders():
        folders[f.getHostDir()] = f.getGuestDir()
     
      builder = {}
      builder["type"] = "virtualbox-iso"
      builder["guest_os_type"] = "Linux_64"
      builder["iso_url"] = "http://releases.ubuntu.com/{0}/{1}".format(instance.getOsVersion(), splittedVersionLine[1])
      builder["iso_checksum_type"] = "md5"
      builder["iso_checksum"] = splittedVersionLine[0].rstrip(" ")
      builder["http_directory"] = "./"
      builder["http_port_min"] = "9000"
      builder["http_port_max"] = "9500"
      builder["ssh_username"] = "vagrant"
      builder["ssh_password"] = "vagrant"
      builder["ssh_wait_timeout"] = "20m"
      builder["headless"] = "true"
      builder["guest_additions_mode"] = "disable"
      builder["shutdown_command"] = "echo 'vagrant' | sudo -E -S shutdown -P now"
      builder["boot_command"] = ["<esc><esc><enter><wait>",
                                  "/install/vmlinuz noapic ",
                                  "preseed/url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/preseed.cfg ",
                                  "debian-installer=en_US auto locale=en_US kbd-chooser/method=us ",
                                  "hostname={0} ".format(instance.getName()),
                                  "fb=false debconf/frontend=noninteractive ",
                                  "keyboard-configuration/modelcode=SKIP keyboard-configuration/layout=FR ",
                                  "keyboard-configuration/variant=USA console-setup/ask_detect=false ",
                                  "initrd=/install/initrd.gz -- <enter>"
      ]        
      instance.getPackerFile()["builders"].append(builder)
      
      postproc = {}
      postproc["type"] = "vagrant-import"
      postproc["import_name"] = instance.getImageName()+"-{{user `hash`}}"
      instance.getPackerFile()["post-processors"].append(postproc)

      shutil.copy(os.path.join(MACHINATION_INSTALLDIR, "share", "machination", "vagrant", "Vagrantfile_virtualbox"), os.path.join(instance.getPath(), "Vagrantfile"))
          
      PROVIDERSLOGGER.debug("Files generated for virtualbox provider.")

    def __str__(self):
      return "virtualbox"
    
    @abstractmethod
    def needsProvisioning(self, instance):
      # virtualbox always needs provisioning
      regex = "{0}-{1}(.*)".format(instance.getImageName(),instance.getTemplateHash())
      p = subprocess.Popen("vagrant box list", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
      out = p.communicate()[0]
      if p.returncode == 0:
        return (re.search(regex, out) == None)
      else:
        raise RuntimeError("Internal error when processing provider of instance '{0}'".format(instance.getName()));

    @abstractmethod
    def generateHashFor(self, instance, hashValue):
      generate_hash_of_file(os.path.join(instance.getPath(), "preseed.cfg"),hashValue)
      
