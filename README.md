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

Machination:
All your appliances are belong to us !

Machination is a simple software helping to create virtual machines for different tasks. 
It relies on a customizable template system that can be applied to instantiate machines.
Currently, only Docker is supported to execute the machines. In the future, Virtualbox will be added.
Installation of software in the machine is handled by Ansible. Again support for additionnal install utilities will be added.

Requirements:
- Vagrant
- Ansible
- Python 2.7
- Enum for Python 2.7
- Host-side-provisioner for vagrant 
 
It features different commands:
- list template|instance:
  This command lists the element handled by machination.

- create <template name> <instance name>:
  This command creates a new instance of a machine. A wizard will be triggered to query
  template's customizable elements.

- destroy <instance name>
  This command destroys an instance All files related to the instance will be deleted
  
- start <instance name>
  This command starts an instance. It must be executed as root because some commands related to network
  needs root authorization in order to be executed.
  
- stop <instance name>
  This command stops an instances. As the start command, it must be ran as root.
  
- ssh <instance name>


When creating a machine, files are stored in the folder ~/.machination. Those files contains the description of the instance. Machine filesystem can also be
stored in this folder depending on the chosen machine provider (Docker or Virtualbox).
When using Docker, the filesystem is stored by the Docker daemon. One shall check where its docker installation stores these files.