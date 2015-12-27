#
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
#
from argparse import ArgumentTypeError
import re
import subprocess
""" Command line module for machination """
from machination.exceptions import InvalidCmdLineArgument
import argparse
import argcomplete
import os
import errno
import traceback

import logging
from distutils.version import StrictVersion
from machination.core import MachineInstance
from machination.loggers import COMMANDLINELOGGER, set_log_level

from machination.questions import BinaryQuestion

from machination.globals import MACHINE_INSTANCE_REGISTRY
from machination.globals import MACHINE_TEMPLATE_REGISTRY
from machination.constants import MACHINATION_VERSIONFILE
from machination.wizards import MachineInstanceCreationWizard

#from machination.helpers import ProgressingTask


class CmdLine(object):

    """ Class used to handle the arguments passed by the command line """

    def __init__(self):
        pass

    @staticmethod
    def list_elements(args):
        """
        Function used to list available templates
        Templates are searched in the install
        directory of machination but also in the user workdir (~/.machination)
        """
        list_functions = {
            "templates": CmdLine.list_machine_templates,
            "instances": CmdLine.list_machine_instances}

        if args.type is None or args.type not in list_functions.keys():
            CmdLine.list_machine_templates(args)
            CmdLine.list_machine_instances(args)
        else:
            list_functions[args.type](args)

    @staticmethod
    def list_machine_templates(_):
        """
        Function used to list available templates
        Templates are searched in the install directory of
        machination but also in the user workdir (~/.machination)
        """
        # Create the template registry that will list all available template on
        # the machine
        COMMANDLINELOGGER.info("Machine templates:")
        COMMANDLINELOGGER.info("-------------------")

        templates = MACHINE_TEMPLATE_REGISTRY.get_templates()
        # Create an array containing a set of informations
        # about the template.
        # This array will be used to display the
        # information to the user
        data = {'name': [],
                'path': [],
                'provisioners': [],
                'providers': [],
                'operating_systems': [],
                'comments': []}
        for template in templates.values():
            data['name'].append(template.get_name())
            data['path'].append(
                os.path.abspath(template.get_path()))
            data['provisioners'].append(
                ",".join([str(s) for s in  template.get_provisioners()]))
            data['providers'].append(
                ",".join([str(s) for s in  template.get_providers()]))
            
            operating_systems = {}
            for operating_sys in template.get_operating_systems():
              if operating_sys.get_name() not in operating_systems:
                operating_systems[operating_sys.get_name()] = []
              operating_systems[operating_sys.get_name()].append(operating_sys.get_architecture())
            
            for operating_sys, archs in operating_systems.items():
              data['operating_systems'].append('{} ({})'.format(operating_sys,
                  ",".join([str(s) for s in archs])))
            
            data['comments'].append(template.get_comments())

        # Getting the max for each column
        name_col_width = max(len(word)
                             for word in data['name'])\
            + len("Name") + 1
        path_col_width = max(len(word)
                             for word in data['path'])\
            + len("Path") + 1
        provisioner_col_width = max(len(word)
                                    for word in data['provisioners'])\
            + len("Provisioners") + 1
        providers_col_width = max(len(word)
                                  for word in data['providers'])\
            + len("Providers") + 1
        os_col_width = max(len(word)
                                      for word in data['operating_systems'])\
            + len("Operating Systems") + 1
        comments_col_width = max(len(word)
                                 for word in data['comments'])\
            + len("Comments") + 1

        # Display the array
        # Checking number of items in the column name to know if there is
        # something to display or not
        if len(data['name']) != 0:
            # Display the array titles
            COMMANDLINELOGGER.info("{}{}{}{}{}{}".format(
                                    "Name".ljust(name_col_width),
                                   "Path".ljust(path_col_width),
                                   "Provisioners".ljust(
                                       provisioner_col_width),
                                   "Providers".ljust(
                                       providers_col_width),
                                   "Operating systems".ljust(
                                       os_col_width),
                                   "Comments").ljust(
                                       comments_col_width))

            for row in range(0, len(data['name'])):
                COMMANDLINELOGGER.info("{}{}{}{}{}{}".format(
                      data['name'][row].ljust(name_col_width),
                      data['path'][row].ljust(path_col_width),
                      data['provisioners'][row].ljust(provisioner_col_width),
                      data['providers'][row].ljust(providers_col_width),
                      data['operating_systems'][row].ljust(os_col_width),
                      data['comments'][row].ljust(comments_col_width)).strip())
        else:
            COMMANDLINELOGGER.info("No templates available")

        COMMANDLINELOGGER.info("")
        return 0

    @staticmethod
    def list_machine_instances(_):
        """
        Function to list the instances
        The instances are searched in the user workdir (~/.machination)
        """
        COMMANDLINELOGGER.info("Machine instances:")
        COMMANDLINELOGGER.info("-------------------")

        instances = MACHINE_INSTANCE_REGISTRY.get_instances()
        COMMANDLINELOGGER.debug("Instances loaded.")

        # Create an array to display the available templates
        data = {'name': [], 'path': [], 'addr': [], 'started': [], 'template': [], 'provider': []}
        for i in instances.values():
            data['name'].append(i.get_name())
            data['path'].append(i.get_path())
            data['template'].append(i.get_template())
            data['provider'].append(str(i.get_provider()))
            data['addr'].append(i.get_infos_at_runtime()[0]["ip"])
            data['started'].append(i.is_started())

        # Display the array of templates
        # Check if there is an item in the resulting array using the length
        # of the column name
        if len(data['name']) != 0:
            name_col_width = max(len(word)
                                 for word in data['name'])\
                + len("Name") + 1
            addr_col_width = max(len(word)
                                 for word in data['addr'])\
                + len("Address") + 1
            path_col_width = max(len(word)
                                 for word in data['path'])\
                + len("Path") + 1
            started_col_width = max(len(str(word))
                                    for word in data['started'])\
                + len("Started") + 1
            template_col_width = max(len(str(word))
                                    for word in data['template'])\
                + len("Template") + 1
            provider_col_width = max(len(str(word))
                                    for word in data['provider'])\
                + len("Provider") + 1

            COMMANDLINELOGGER.info("{}{}{}{}{}{}".format(
                "Name".ljust(name_col_width),
                "Started".ljust(started_col_width),
                "Address".ljust(addr_col_width),
                "Path".ljust(path_col_width),
                "Provider".ljust(provider_col_width),
                "Template".ljust(template_col_width)
                )
                )
            for row in range(0, len(data['name'])):
                COMMANDLINELOGGER.info("{}{}{}{}{}{}".format(
                  data['name'][row].ljust(name_col_width),
                  str(data['started'][row]).ljust(started_col_width),
                  data['addr'][row].ljust(addr_col_width),
                  data['path'][row].ljust(path_col_width),
                  data['provider'][row].ljust(provider_col_width),
                  data['template'][row].ljust(template_col_width)
                  ))
        else:
            COMMANDLINELOGGER.info("No instances available")
        COMMANDLINELOGGER.info("")
        return 0

    @staticmethod
    def print_infos(instance):
        COMMANDLINELOGGER.info("Machine '{}':".format(instance.get_name()))
        COMMANDLINELOGGER.info("  Architecture: {}".format(instance.get_operating_system().get_architecture()))
        COMMANDLINELOGGER.info("  Operating sytem: {}".format(instance.get_operating_system().get_name()))
        COMMANDLINELOGGER.info("  Provisioner: {}".format(instance.get_provisioner()))
        COMMANDLINELOGGER.info("  Provider: {}".format(instance.get_provider()))
        COMMANDLINELOGGER.info("  State: {}".format("Running" if instance.is_started() else "Stopped"))
        COMMANDLINELOGGER.info("  Host interface: {}".format(instance.get_host_interface()))
        if len(instance.get_shared_folders()) != 0:
            COMMANDLINELOGGER.info("  Shared folders:")
            for folder in instance.get_shared_folders():
                COMMANDLINELOGGER.info("    - Host folder: \
                  {}".format(folder.get_host_dir()))
                COMMANDLINELOGGER.info("      Guest folder: \
                  {}".format(folder.get_guest_dir()))
        
        infos = instance.get_infos_at_runtime()
        COMMANDLINELOGGER.info("  Network interfaces:")
        for info in infos:
          COMMANDLINELOGGER.info("    - Name: {}".format(info["name"]))
          COMMANDLINELOGGER.info("      IPAddress: {}".format(info["ip"]))
          COMMANDLINELOGGER.info("      MACAddress: {}".format(info["mac"]))
          COMMANDLINELOGGER.info("      Host interface: {}".format(info["host_interface"]))
          COMMANDLINELOGGER.info("      Hostname: {}".format(info["hostname"]))
      
    @staticmethod
    def create_machine_instance(args):
        """
        Function to create a new machine
        """
        res = 0
        COMMANDLINELOGGER.info(
            "Creating a new instance named '{}' using template '{}'".format(
                args.name,
                args.template))
        # Creating the template and instances registries
        # progress_bar = ProgressingTask()
        # Get templates
        templates = MACHINE_TEMPLATE_REGISTRY.get_templates()
        COMMANDLINELOGGER.debug("Templates loaded.")
        # Get instances
        instances = MACHINE_INSTANCE_REGISTRY.get_instances()
        COMMANDLINELOGGER.debug("Instances loaded.")

        try:
            # Try to create the new machine
            # Check if the instance is already in the registry
            if args.force:
                if args.name in instances.keys():
                    COMMANDLINELOGGER.warn(
                        "Instance named '{}' already exists but creation \
was forced so firstly machination will delete it.".format(args.name))
                    #progress_bar.start()
                    instances[args.name].destroy()
                    #progress_bar.stop()

            if args.force == False and args.name in instances.keys():
                COMMANDLINELOGGER.error(
                    "Unable to create machine: an instance named '{}' \
already exists. Change the name of your new machine or\
delete the existing one.".format(args.name))
                res = errno.EALREADY
            else:
                (template, operating_system, provider,
                 provisioner, guest_interfaces,
                 host_interface, shared_folders) = \
                    MachineInstanceCreationWizard().execute(args, templates)
                instance = MachineInstance(
                    args.name,
                    template,
                    operating_system,
                    provider,
                    provisioner,
                    guest_interfaces,
                    host_interface,
                    shared_folders,
                    None)

                #progress_bar.appendLines(
                #   {".*Provisioning with shell script.*": [50, None]})
                #progress_bar.appendLines(
                #    {".*Running post-processor.*": [80, None]})
                #progress_bar.start()
                instance.create()
                #progress_bar.stop()
                CmdLine.print_infos(instance)
                COMMANDLINELOGGER.info(
                    "Instance '{}' successfully created.".format(args.name))
        except (RuntimeError, InvalidCmdLineArgument) as excpt:
            COMMANDLINELOGGER.error(
                "Unable to create instance '{}': \
                {}.".format(args.name, str(excpt)))
            if not args.verbose:
                COMMANDLINELOGGER.info(
                    "Run with --verbose flag for more details")
            COMMANDLINELOGGER.debug(traceback.format_exc())
            res = errno.EINVAL
        return res

    @staticmethod
    def destroy_machine_instance(args):
        """
        Function to destroy a machine
        Files related to the machine are deleted
        """
        res = 0
        for name in args.names:
            try:
                # Getting instances
                instances = MACHINE_INSTANCE_REGISTRY.get_instances()
                # Check if there is actually an instance named after the
                # request of the user
                if name in instances.keys():
                    # Ask the user if it's ok to delete the machine
                    is_verbose = args.force
                    if is_verbose == False:
                        is_verbose = BinaryQuestion("Are you sure you want \
to destroy the machine named {}. Directory {})\
will be destroyed".format(
                            instances[name].get_name(),
                            instances[name].get_path()),
                                                    "Enter a Y or a N",
                                                    COMMANDLINELOGGER, "Y")\
                            .ask()
                    if is_verbose:
                        COMMANDLINELOGGER.info(
                            "Destroying instance '{}'...".format(name))
                        instances[name].destroy()
                        COMMANDLINELOGGER.info(
                            "Instance '{}' successfully \
                            destroyed".format(name))
                    else:
                        COMMANDLINELOGGER.info(
                            "Instance '{}' not destroyed".format(name))
                else:
                    COMMANDLINELOGGER.error(
                        "Instance '{}' does not exist.".format(name))
                    res = errno.EINVAL
            except RuntimeError as excpt:
                COMMANDLINELOGGER.error(
                    "Unable to destroy instance \
                    '{}': {}".format(name, str(excpt)))
                if not args.verbose:
                    COMMANDLINELOGGER.info(
                        "Run with --verbose flag for more details")
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
            except (KeyboardInterrupt, SystemExit):
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
        return res

    @staticmethod
    def start_machine_instance(args):
        """
        Function to start a machine
        The user must be root to call this function as some \
        stuff related to networking needs to be executed as root
        """
        res = 0
        for name in args.names:
            COMMANDLINELOGGER.info("Starting instance {}".format(name))
            try:
                # Getting the available instances
                instances = MACHINE_INSTANCE_REGISTRY.get_instances()
                # Check if the requested instance exists
                if name in instances.keys():
                    instances[name].start()
                else:
                    COMMANDLINELOGGER.error(
                        "Instance '{}' does not exist.".format(name))
                    res = errno.EINVAL
                COMMANDLINELOGGER.info(
                    "Instance '{}' successfully started.".format(name))
            except RuntimeError as excpt:
                COMMANDLINELOGGER.error(
                    "Unable to start instance '{}': \
                    {}.".format(name, str(excpt)))
                COMMANDLINELOGGER.debug(traceback.format_exc())
                if not args.verbose:
                    COMMANDLINELOGGER.info(
                        "Run with --verbose flag for more details")
                res = errno.EINVAL
            except (KeyboardInterrupt, SystemExit):
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
        return res

    @staticmethod
    def update_machine_instance(args):
        """
        Run apt-get update and upgrade on the machine
        """
        res = 0
        for name in args.names:
            COMMANDLINELOGGER.info("Updating instance {}".format(name))
            try:
                # Getting the available instances
                instances = MACHINE_INSTANCE_REGISTRY.get_instances()
                # Check if the requested instance exists
                if name in instances.keys():
                    if not instances[args.name].is_started():
                        COMMANDLINELOGGER.error(
                            "Instance '{}' is not started, starting it \
before update process.".format(args.name))
                        instances[args.name].start()
                    try:
                        instances[args.name].ssh(
                            "sudo apt-get update && sudo apt-get dist-upgrade")
                        COMMANDLINELOGGER.error(
                            "Instance '{}' successfuly \
                            updated.".format(args.name))
                    except RuntimeError as excpt:
                        COMMANDLINELOGGER.error(
                            "Unable to update instance '{}'. \
                            Please try manually.".format(args.name))
                else:
                    COMMANDLINELOGGER.error(
                        "Instance '{}' does not exist.".format(name))
                    res = errno.EINVAL
                COMMANDLINELOGGER.info(
                    "Instance '{}' successfully started.".format(name))
            except RuntimeError as excpt:
                COMMANDLINELOGGER.error(
                    "Unable to start instance '{}': \
                    {}.".format(name, str(excpt)))
                COMMANDLINELOGGER.debug(traceback.format_exc())
                if not args.verbose:
                    COMMANDLINELOGGER.info(
                        "Run with --verbose flag for more details")
                res = errno.EINVAL
            except (KeyboardInterrupt, SystemExit):
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
        return res

    @staticmethod
    def stop_machine_instance(args):
        """
        Function to stop a machine
        User must be root to call this function juste to be
        symetric with the start operation
        """
        res = 0
        for name in args.names:
            COMMANDLINELOGGER.info("Stopping instance {}".format(name))
            try:
                instances = MACHINE_INSTANCE_REGISTRY.get_instances()
                # Search for the requested instnce
                if name in instances.keys():
                    instances[name].stop()
                else:
                    COMMANDLINELOGGER.error(
                        "Instance '{}' does not exist.".format(name))
                COMMANDLINELOGGER.info(
                    "Instance '{}' successfully stopped.".format(name))
            except RuntimeError as excpt:
                COMMANDLINELOGGER.error(
                    "Unable to stop instance '{}': \
                    {}.".format(name, str(excpt)))
                if not args.verbose:
                    COMMANDLINELOGGER.info(
                        "Run with --verbose flag for more details")
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
            except (KeyboardInterrupt, SystemExit):
                COMMANDLINELOGGER.debug(traceback.format_exc())
                res = errno.EINVAL
        return res

    @staticmethod
    def restart_machine_instance(args):
        """
        Function to restart a machine
        User must be root to call this function juste to be \
        symetric with the start and stop operations
        """
        CmdLine.stop_machine_instance(args)
        return CmdLine.start_machine_instance(args)

    @staticmethod
    def get_machine_instance_infos(args):
        """
        Function to get infos from a machine instance
        """
        res = 0
        to_display = []
        if args.names:
            to_display.append(args.names)

        instances = MACHINE_INSTANCE_REGISTRY.get_instances()

        if len(to_display) == 0:
            to_display = instances.keys()

        for name in to_display:
            # Search for the requested instnce
            if name in instances.keys():
                CmdLine.print_infos(instances[name])
            else:
                COMMANDLINELOGGER.error(
                    "Instance '{}' does not exist.".format(name))
                res = errno.EINVAL
        return res

    @staticmethod
    def ssh_into_machine_instance(args):
        """
        Function to connect to the machine in SSH
        """
        res = 0
        COMMANDLINELOGGER.info("SSH into machine {}".format(args.name))
        try:
            # Search for the requested instance in the registry
            instances = MACHINE_INSTANCE_REGISTRY.get_instances()
            if args.name in instances.keys():
                if not instances[args.name].is_started():
                    COMMANDLINELOGGER.error(
                        "Instance '{}' is not started, starting it \
before connecting to it.".format(args.name))
                    instances[args.name].start()

                instances[args.name].ssh(args.command)
            else:
                COMMANDLINELOGGER.error(
                    "Instance '{}' does not exist.".format(args.name))
        except RuntimeError as excpt:
            COMMANDLINELOGGER.error(
                "Unable to SSH into instance '{}': ".format(str(excpt)))
            if not args.verbose:
                COMMANDLINELOGGER.info(
                    "Run with --verbose flag for more details")
            COMMANDLINELOGGER.debug(traceback.format_exc())
            res = errno.EINVAL
        except (KeyboardInterrupt, SystemExit):
            COMMANDLINELOGGER.debug(traceback.format_exc())
        return res

    @staticmethod
    def display_version(_):
        """
        Display the machination's version
        """
        version = "Unknown version"
        try:
            version_file = open(MACHINATION_VERSIONFILE, 'r')
            version = StrictVersion(version_file.read())
        except ValueError:
            pass
        COMMANDLINELOGGER.info("Machination {}".format(str(version)))

    @staticmethod
    def initialize_arguments_parser():
        """
        Initialize the argument parser
        """
        templates = MACHINE_TEMPLATE_REGISTRY.get_templates()
        instances = MACHINE_INSTANCE_REGISTRY.get_instances()

        def MachineInstanceName(v):
          try:
            return re.match("^[1-9a-zA-Z-]*$", v).group(0)
          except:
            raise ArgumentTypeError("Machine instance name '{}' shall contain \
only numbers, letters and hyphens".format(v))
            
        # Create main parser
        parser = argparse.ArgumentParser(
            prog="Machination",
            description='Machination utility, all your \
          appliances belong to us.')

        root_subparsers = parser.add_subparsers(dest="function")
        root_subparsers.add_parser('version', help='Display version')

        # Parser for list command
        list_parser = root_subparsers.add_parser(
            'list',
            help='List templates and instances')
        list_parser.add_argument(
            'type',
            help='Type to list',
            nargs='?',
            type=str,
            choices=("templates",
                     "instances"))
        list_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for create command
        create_parser = root_subparsers.add_parser(
            'create',
            help='Create the given machine in the path')
        create_parser.add_argument(
            'template',
            help='Name of the template to create',
            type=str,
            choices=templates.keys())
        create_parser.add_argument(
            'name',
            help='Name of the machine to create',
            type=MachineInstanceName)
        
        create_parser.add_argument(
            '--architecture',
            '-a',
            help='Architecture to use',
            type=str)
        create_parser.add_argument(
            '--provider',
            '-p',
            help='Provider to use',
            type=str)
        create_parser.add_argument(
            '--provisioner',
            '-n',
            help='Provisioner to use',
            type=str)
        create_parser.add_argument(
            '--operatingsystem',
            '-o',
            help='Operating system name',
            type=str)
        create_parser.add_argument(
            '--guestinterface',
            '-i',
            help='Network interface to add',
            metavar="<host_interface>,<ip_addr>[,mac_addr,hostname]",
            action='append',
            type=str)
        create_parser.add_argument(
            '--sharedfolder',
            '-s',
            nargs=2,
            help='Shared folder between the new machine and the host',
            metavar=("<host folder>",
                     "<guest folder>"),
            action='append',
            type=str)
        create_parser.add_argument(
            '--no-interactive',
            help='Do not request for interactive configuration of \
          optional elements (interfaces,sharedfolders)',
            action='store_true')
        create_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')
        create_parser.add_argument(
            '--force',
            "-f",
            help='Force creation by deleting an instance with same name',
            action='store_true')

        # Parser for destroy command
        destroy_parser = root_subparsers.add_parser(
            'destroy',
            help='Destroy the given machine in the path')
        destroy_parser.add_argument(
            'names',
            help='Name of the machine to destroy',
            nargs="+",
            type=MachineInstanceName,
            choices=instances.keys())
        destroy_parser.add_argument(
            '--force',
            '-f',
            help='Do not ask for confirmation',
            action='store_true')
        destroy_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for start command
        start_parser = root_subparsers.add_parser(
            'start',
            help='Start the given machine instance')
        start_parser.add_argument(
            'names',
            help='Name of the machine to start',
            nargs="+",
            type=MachineInstanceName,
            choices=instances.keys())
        start_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for stop command
        stop_parser = root_subparsers.add_parser(
            'stop',
            help='Stop the given machine instance')
        stop_parser.add_argument(
            'names',
            help='Name of the machine to stop',
            nargs="+",
            type=MachineInstanceName,
            choices=instances.keys())
        stop_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for restart command
        restart_parser = root_subparsers.add_parser(
            'restart',
            help='Restart the given machine instance')
        restart_parser.add_argument(
            'names',
            help='Name of the machine to restart',
            nargs="+",
            type=MachineInstanceName,
            choices=instances.keys())
        restart_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for infos command
        infos_parser = root_subparsers.add_parser(
            'infos',
            help='Get informations about a machine instance')
        infos_parser.add_argument(
            'names',
            help='Name of the machine instance from which \
          infos shall be retrieved',
            nargs="?",
            type=MachineInstanceName,
            choices=instances.keys())
        infos_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')

        # Parser for ssh command
        ssh_parser = root_subparsers.add_parser(
            'ssh', help='SSH to the given machine')
        ssh_parser.add_argument(
            'name',
            help='Name of the machine to ssh in',
            choices=instances.keys(),
            type=MachineInstanceName)
        ssh_parser.add_argument(
            '--command',
            "-c",
            help='Command to execute in SSH',
            type=str)
        ssh_parser.add_argument(
            '--verbose',
            "-v",
            help='Verbose mode',
            action='store_true')
        return parser

    @staticmethod
    def parse_args(args):
        """
        Function to parse the command line arguments
        """
        # Create main parser
        parser = CmdLine.initialize_arguments_parser()
        # Parse the command
        argcomplete.autocomplete(parser)
        args = parser.parse_args()

        functions = {
            "list": CmdLine.list_elements,
            "create": CmdLine.create_machine_instance,
            "destroy": CmdLine.destroy_machine_instance,
            "start": CmdLine.start_machine_instance,
            "stop": CmdLine.stop_machine_instance,
            "restart": CmdLine.restart_machine_instance,
            "infos": CmdLine.get_machine_instance_infos,
            "ssh": CmdLine.ssh_into_machine_instance,
            "version": CmdLine.display_version
        }

        if "verbose" in args and args.verbose:
            set_log_level(logging.DEBUG)
        else:
            set_log_level(logging.INFO)

        res = errno.EINVAL
        try:
            if args.function in functions.keys():
                res = functions[args.function](args)
        except (KeyboardInterrupt, SystemExit):
            COMMANDLINELOGGER.debug(traceback.format_exc())
            res = errno.EINVAL
        return res
