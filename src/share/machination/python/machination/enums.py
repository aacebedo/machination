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

from enum import Enum
from machination.helpers import accepts
from machination.filegenerators import AnsibleProvisionerFileGenerator
from machination.exceptions import InvalidArgumentValue

class StringifiedEnum(Enum):  
    def __str__(self):
        return str(self.value)

class Provider(StringifiedEnum):
    Docker = "Docker"
    
    @staticmethod
    @accepts(StringifiedEnum)
    def fromString(val):
        vals = {
                "Docker" : Provider.Docker,
                }
        if val in vals:
            return vals[val]
        else:
            raise InvalidArgumentValue("Unknown provider")
        
        
class Provisioner(StringifiedEnum):
    Ansible = "Ansible"
    
    @staticmethod
    def getFileGenerator(pro):
        ctrs = {
            Provisioner.Ansible : AnsibleProvisionerFileGenerator
                        }
        if pro in ctrs:
            return ctrs[pro]()
        else:
            raise InvalidArgumentValue("Unknown provisioner")
    
    @staticmethod
    @accepts(str)
    def fromString(val):
        vals = {
                "Ansible" : Provisioner.Ansible,
                }
        if val in vals:
            return vals[val]
        else:
            raise InvalidArgumentValue("Unknown provisioner")


class Architecture(StringifiedEnum):
    x86 = "x86"
    x64 = "x64"
    
    @staticmethod
    @accepts(str)
    def fromString(val):
        vals = {
                "x86" : Architecture.x86,
                "x64" : Architecture.x64
                }
        if val in vals:
            return vals[val]
        else:
            raise InvalidArgumentValue("Unknown architecture")