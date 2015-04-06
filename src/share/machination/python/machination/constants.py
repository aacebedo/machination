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

# Path of the program files
MACHINATION_INSTALLDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..",'..','..','..'))
MACHINATION_DEFAULTTEMPLATESDIR = os.path.abspath(os.path.join(MACHINATION_INSTALLDIR,"etc","defaults","machination","templates"))
MACHINATION_DEFAULTPROVISIONERSDIR = os.path.abspath(os.path.join(MACHINATION_INSTALLDIR,"etc","defaults","machination","provisioners"))
MACHINATION_DEFAULTANSIBLEPLAYBOOKSDIR = os.path.join(MACHINATION_DEFAULTPROVISIONERSDIR,"ansible","playbooks")
MACHINATION_DEFAULTANSIBLEROLESDIR = os.path.join(MACHINATION_DEFAULTPROVISIONERSDIR,"ansible","roles")


# User dir to store instances and templates
MACHINATION_USERDIR = os.path.abspath(os.path.join(os.path.expanduser("~"),".machination"))
MACHINATION_USERINSTANCESDIR = os.path.join(MACHINATION_USERDIR,"instances")
MACHINATION_USERTEMPLATESDIR = os.path.join(MACHINATION_USERDIR,"templates")
MACHINATION_USERPROVISIONERSDIR = os.path.join(MACHINATION_USERDIR,"provisioners")
MACHINATION_USERANSIBLEPLAYBOOKSDIR = os.path.join(MACHINATION_USERPROVISIONERSDIR,"ansible","playbooks")
MACHINATION_USERANSIBLEROLESDIR = os.path.join(MACHINATION_USERPROVISIONERSDIR,"ansible","roles")

MACHINATION_CONFIGFILE_NAME="machine_instance_config.yml"