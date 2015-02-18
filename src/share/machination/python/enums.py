from enum import Enum

class StringifiedEnum(Enum):  
    def __str__(self):
        return str(self.value)

class Provider(StringifiedEnum):
    Docker = "Docker"
     
class Provisioner(StringifiedEnum):
    Ansible = "Ansible"
    
class Architecture(StringifiedEnum):
    x86 = "i386"
    x64 = "x64"