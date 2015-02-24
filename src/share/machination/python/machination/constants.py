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
MACHINATION_BASEPROVISIONERSDIR = os.path.abspath(os.path.join(MACHINATION_INSTALLDIR,"share","machination","provisioners"))
MACHINATION_BASEPROVIDERSDIR = os.path.abspath(os.path.join(MACHINATION_INSTALLDIR,"share","machination","providers"))

# User dir to store instances and templates
MACHINATION_USERDIR = os.path.abspath(os.path.join(os.path.expanduser("~"),".machination"))
MACHINATION_USERINSTANCESDIR = os.path.join(MACHINATION_USERDIR,"instances")
MACHINATION_USERTEMPLATEDIR = os.path.join(MACHINATION_USERDIR,"templates")

MACHINATION_USERPROVISIONERSDIR = os.path.join(MACHINATION_USERDIR,"provisioners")