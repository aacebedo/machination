# Machination
All your appliances are belongs to us !

Machination helpsy you to create virtual machines running with vagrant.
It relies on a customizable template system that can be applied to instantiate machines.
Currently, only Docker is supported to execute the machines. In the future, Virtualbox will be added.
Installation of software in the machine is handled by Ansible. Again support for additionnal install utilities will be added.

### Requirements
- Vagrant 1.7.2
- Ansible 1.7.2
- Python 2.7.8
- Docker 1.4.1
- Enum for Python 2.7
- Host-side-provisioner for vagrant (https://github.com/phinze/vagrant-host-shell)
- Docker's pipework (https://github.com/jpetazzo/pipework)

### Installation
```sh
$ tar xvzf machination.tar.gz
$ cd machination
$ ./waf configure --prefix=<install_prefix>
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