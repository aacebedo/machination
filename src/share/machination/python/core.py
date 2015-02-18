import os
from enums import *
import yaml
from constants import *
import subprocess
import sys 
from helpers import *
import pwd
import shutil
import inspect        
class NetworkInterface(yaml.YAMLObject):
    yaml_tag = "!NetworkInterface"
    _ipAddr = None
    _macAddr = None
    _hostname = None

    def __init__(self,ipAddr, macAddr,hostname=None):
        self._ipAddr = ipAddr
        self._macAddr = macAddr
        self._hostname = hostname

    def getIPAddr(self):
        return self._ipAddr
    
    def setIPAddr(self,val):
        self._ipAddr = val
        
    def getMACAddr(self):
        return self._macAddr
    
    def setMACAddr(self,val):
        self._macAddr = val
    
    def getHostname(self):
        return self._hostname
    
    def setHostname(self,val):
        self._hostname = val

    def __str__(self):
        res = ""
        if self._hostname != None :
            res = self._hostname + "|"
            
        return res + self.getIPAddr()+"|"+self.getMACAddr()
    
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "ipaddr" : data.getIPAddr(),
                           "macaddr" : data.getMACAddr()
                           }
        if data.getHostname()!=None:
            representation["hostname"] = data.getHostname()
        
        return dumper.represent_mapping(data.yaml_tag,representation)

class SyncedFolder(yaml.YAMLObject):
    yaml_tag = "!SyncedFolder"
    _hostDir = None
    _guestDir = None

    def __init__(self,host_dir,guest_dir):
        self._hostDir = host_dir
        self._guestDir = guest_dir

    def getHostDir(self):
        return self._hostDir
    
    def setHostDir(self,val):
        self._hostDir = val
        
    def getGuestDir(self):
        return self._guestDir
    
    def setGuestDir(self,val):
        self._guestDir = val

    def __str__(self):
        res = ""            
        return self._hostDir + " => " + self._guestDir
    
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                           "host_dir" : data.getHostDir(),
                           "guest_dir" : data.getGuestDir()
                           }
        return dumper.represent_mapping(data.yaml_tag,representation) 
       
        
        
class InvalidMachineTemplateError:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)
    
class MachineTemplate(yaml.YAMLObject):
    yaml_tag = '!MachineTemplate'
    path = None
    provisioners = []
    providers = []
    os_versions = []
    archs = []
    guest_interfaces = []
    
    def __init__(self, path, archs, os_versions ,providers, provisioners, guest_interfaces):
        self.path = path
        self.archs = archs
        self.os_versions = os_versions
        self.providers = providers
        self.provisioners = provisioners
        self.guest_interfaces = guest_interfaces
                                                      
#         self.path = os.path.abspath(path)
#         stream = open(self.path)
#         self.desc = yaml.load(stream)           
#         if "archs" in self.desc.keys():            
#             for p in self.desc["archs"]:
#                 if not p in Architecture.__members__.keys():
#                     raise InvalidMachineTemplateError("arch value")
#                 else:
#                     self._archs.append(Architecture[p])
#         else:
#             raise InvalidMachineTemplateError("archs")
#         
#         if  "providers" in self.desc.keys() and isinstance(self.desc["providers"], list) and len(self.desc["providers"]) :
#             for p in self.desc["providers"]:
#                 if not p in Provider.__members__.keys():
#                     raise InvalidMachineTemplateError("provider value")
#                 else:
#                     self._providers.append(Provider[p])
#         else:
#             raise InvalidMachineTemplateError("providers")        
#                    
#         if "provisioners" in self.desc.keys() and isinstance(self.desc["provisioners"], list) and len(self.desc["provisioners"]) != 0 :
#             for p in self.desc["provisioners"]:
#                 if not p in Provisioner.__members__.keys():
#                     raise InvalidMachineTemplateError("provisioners value")
#                 else:
#                     self._provisioners.append(Provisioner[p])
#         else:
#             raise InvalidMachineTemplateError("provisioners")
# 
#         if  "os_version" in self.desc.keys() and isinstance(self.desc["providers"], list) and len(self.desc["providers"]) :
#             for p in self.desc["os_version"]:
#                 self._providers.append(p)
#         else:
#             raise InvalidMachineTemplateError("os_version")        
# 
#         if "guest_interfaces" in self.desc.keys() and isinstance(self.desc["guest_interfaces"], list):
#             for p in self.desc["guest_interfaces"]:
#                 if p.has_key("ipaddr"):
#                     macAddr = randomMAC()
#                     if  p.has_key("macaddr"):
#                         macAddr = p["macaddr"]
#                     if p.has_key("hostname"):
#                         self._guestInterfaces.append(NetworkInterface(p["ipaddr"],macAddr,p["hostname"]))
#                     else:
#                         self._guestInterfaces.append(NetworkInterface(p["ipaddr"],macAddr))
#                 else:
#                     raise InvalidMachineTemplateError("size")
#         else:
#             raise InvalidMachineTemplateError("guest_interfaces")
        
    def getName(self):
        print(self.path)
        fileName = os.path.basename(self.path)
        return os.path.splitext(fileName)[0]
    
    def getPath(self):
        return self.path
    
    def getArchs(self):
        return self.archs
    
    def getProviders(self):
        return self.providers
    
    def getProvisioners(self):
        return self.provisioners

    def getOsVersions(self):
        return self.os_versions
    
    def getGuestInterfaces(self):
        return self.guest_interfaces
    
    @classmethod
    def to_yaml(cls, dumper, data):           
        representation = {
                            "path" : data.path,
                            "archs" : data.archs,
                            "os_versions" : str(data.os_versions),
                            "providers" : str(data.providers),
                            "provisioners" : str(data.provisioners),
                            "guest_interfaces" : data.guest_interfaces,
                            }
        node = dumper.represent_mapping(data.yaml_tag,representation)    
        return node
    
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node)
        archs = []
        print(node)
        print(representation["providers"])
        for p in representation["archs"]:
            if not p in Architecture.__members__.keys():
                raise InvalidMachineTemplateError("arch value")
            else:
                archs.append(Architecture[p])
        
        providers = []
        for p in representation["providers"]:
            if not p in Provider.__members__.keys():
                raise InvalidMachineTemplateError("arch value")
            else:
                archs.append(Provider[p])
        
        provisioners = []
        for p in representation["provisioners"]:
            if not p in Provisioner.__members__.keys():
                raise InvalidMachineTemplateError("provisioner value")
            else:
                archs.append(Provisioner[p])
        
        return MachineTemplate(loader.stream.name,                
                               archs, 
                               representation["os_versions"],                                
                               providers,
                               provisioners,  
                               representation["guest_interfaces"])
        

class MachineInstance(yaml.YAMLObject):
    yaml_tag = '!MachineInstance'
    name = None
    template = None
    provisioner = None  # Provisioner.Ansible
    provider = None  # Provider.Ansible    
    os_version = None
    host_interface = None
    guest_interfaces  = None
    arch = None
    synced_folders = None
    
    def __init__(self, name, template, arch,os_version,provider, provisioner, host_interface, guest_interfaces,synced_folders):
        self.name = name
        self.template = template
        self.arch = arch
        self.os_version = os_version
        self.provider = provider
        self.provisioner = provisioner
        self.guest_interfaces = guest_interfaces
        self.host_interface = host_interface   
        self.synced_folders = synced_folders
        
    def getPath(self):
        return os.path.join(MACHINATION_USERDIR,"instances",self.getName())
    
    def instantiate(self):
        if not os.path.exists(self.getPath()):
            os.makedirs(self.getPath())
        if not os.path.islink(os.path.join(self.getPath(),"Vagrantfile")):
            os.symlink(os.path.join(MACHINATION_INSTALLDIR,"share","machination","vagrant","Vagrantfile"),os.path.join(self.getPath(),"Vagrantfile"))
        else:
            v = raw_input("Vagrant file already exists in the indicate folder do you want to overwrite it ? [Y/n]: ")
        configFile = yaml.dump(self)
        file = open(os.path.join(self.getPath(),"config.yml"),"w+")
        file.write(configFile)
        file.close()
        pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
        os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)
        for root, dirs, files in os.walk(self.getPath()):  
            for d in dirs:  
                os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
            for f in files:
                os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)
                    
    def getName(self):
        return self.name
            
    def getSharedFolders(self):
        return self.shared_folders
    
    def setSharedFolders(self,val):
        self.shared_folders = val
 
    def start(self):
        pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR        
        instanceEnv = os.environ.copy()
        #subprocess.Popen("vagrant up", shell=True, preexec_fn=demote(pw_record.pw_uid, pw_record.pw_gid), stdout=subprocess.PIPE, env=instanceEnv,cwd=self.getPath()).stdout.read()              
        subprocess.Popen("vagrant up", shell=True, stdout=subprocess.PIPE,env=instanceEnv,cwd=self.getPath()).stdout.read()
        os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)        
        for root, dirs, files in os.walk(self.getPath()):  
            for d in dirs:  
                os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
            for f in files:
                os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)
  
    def destroy(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR        
        subprocess.Popen("vagrant destroy -f", shell=True, stdout=subprocess.PIPE,cwd=self.getPath()).stdout.read()
        shutil.rmtree(self.getPath())
              
    def stop(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        subprocess.Popen("vagrant halt", shell=True, stdout=subprocess.PIPE, env=instanceEnv,cwd=self.getPath()).stdout.read()              

    def ssh(self):
        os.environ["MACHINATION_INSTALLDIR"] = MACHINATION_INSTALLDIR
        instanceEnv = os.environ.copy()
        val = subprocess.Popen("vagrant ssh", shell=True, env=instanceEnv, stderr=subprocess.PIPE, cwd=self.getPath())
        while True:
            out = val.stderr.read(1)
            if out == '' and val.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
                
    @classmethod
    def to_yaml(cls, dumper, data):           
        representation = {
                               "name" : data.name,
                               "template" : data.template.getName(),
                               "arch" : str(data.arch),
                               "os_version" : str(data.os_version),
                               "provider" : str(data.provider),
                               "provisioner" : str(data.provisioner),
                               "host_interface" : data.host_interface,
                               "guest_interfaces" : data.guest_interfaces,
                               "synced_folders" :  data.synced_folders,
                               }
        node = dumper.represent_mapping(data.yaml_tag,representation)    
        return node
    
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node)        
        return MachineInstance(representation['name'], 
                               representation["template"],
                               representation["arch"], 
                               representation["os_version"],                                
                               representation["provider"],
                               representation["provisioner"], 
                               representation["host_interface"], 
                               representation["guest_interfaces"],
                               representation["synced_folders"])