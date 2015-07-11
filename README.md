# Machination
All your appliances are belongs to us !

Machination helps you to create virtual machines running with vagrant.
It relies on a customizable template system that can be applied to instantiate machines.
Currently, only Docker is supported to execute the machines. Adding Virtualbox is a work in progress.
Installation of software in the machine is handled by Ansible. Again support for additionnal install utilities will be added.

### Requirements
- Vagrant 1.7.0 (www.vagrantup.com)
- Ansible 1.7.2 (www.ansible.com)
- Python 2.7.8
- Docker 1.4.1
- Packer 0.8.1 (www.packer.io)
- Udhcpc (dhcp client) 
- Enum34 for Python 2.7
- Argcomplete for Python 2.7 (allows tab autocomplete)
- Host-side-provisioner for vagrant (https://github.com/phinze/vagrant-host-shell)
- Docker's pipework (https://github.com/jpetazzo/pipework)

### Principle
Machination is based on templates (overcoming docker main limitation: passing arguments and/or sharing parts of dockerfiles).

A template define:
- the provider (provides the virtual infrastructure): docker
- the provisioner (executes installation instructions): ansible
- the system version (ubuntu trusty, vivid,...)
- optionnal additionnal network interfaces
- the role(s) of the machine
The file is named <templateName>.template

Each template can pick from different roles.
For example, the build env may depend from the role "build-gcc", and the dev-env may depend from "build-gcc" and "xDevTools".
Note: the roles are then executed in order of their listing (and can depend themselves on other roles).

### Installation
```sh
$ tar xvzf machination.tar.gz
$ cd machination
$ ./waf configure --prefix=<install_prefix> --templates=<templates_to_install>
$ ./waf build
```
### Commands
List the available templates or instances:
```sh
$ machination list templates|instances
```
Create an instance using the machination's wizard:
```sh
$ machination create <template_name> <instance_name>
```
Note: The wizard will ask you question depending on the template you've chosen.
Destroy an instance (all files will be deleted):
```sh
$ machination destroy <instance_name>
```
Start an instance:
```sh
$ machination start <instance_name>
```
Stop an instance:
```sh
$ machination stop <instance_name>
```
SSh to an instance:
```sh
$ machination ssh <instance_name>
```

When creating a machine, files are stored in the folder ~/.machination. Those files contains the description of the instance. Machine filesystem can also be
stored in this folder depending on the chosen machine provider (Docker or Virtualbox).
When using Docker, the filesystem is stored by the Docker daemon. One shall check where its docker installation stores these files.

### Additional infos
When creating a machine, files are stored in the folder ~/.machination. Those files contains the description of the instance.
When using Docker, the filesystem is stored by the Docker daemon. One shall check where its docker installation stores these files when maintenance operations needs to be done.

### Todo's
 - Add Virtualbox support

License
----
LGPL
