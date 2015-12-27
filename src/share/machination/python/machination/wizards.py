'''
Created on Aug 22, 2015

@author: vagrant
'''
import machination
from machination.exceptions import InvalidCmdLineArgument,\
  InvalidHardwareSupport
from machination.questions import RegexedQuestion, BinaryQuestion, PathQuestion
from machination.loggers import COMMANDLINELOGGER
from machination.providers import Provider
from machination.provisioners import Provisioner
from machination.enums import Architecture
from machination.helpers import get_all_net_interfaces
from machination.core import NetworkInterface, SharedFolder, OperatingSystem

class MachineInstanceCreationWizard:
  def unpackInterface(self,strCmdLine):
    pack = strCmdLine.split(',')
    if len(pack)==3:
      (ipAddr,macAddr,hostname) = pack
    elif len(pack)==2:
      (ipAddr,macAddr,hostname) = pack + [None]
    else:
        raise InvalidCmdLineArgument("guestinterface", strCmdLine )
    if(macAddr == "auto" or macAddr == None):
        macAddr = machination.helpers.generate_random_mac()
    print((ipAddr,macAddr,hostname))
    return (ipAddr,macAddr,hostname)
  
  
  def requestGuestInterface(self,networkInterfaces):
    hostnameRegex = "([0-9a-zA-Z]*)"
    ipAddrRegex = "(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp"
    macAddrRegex = "([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})"
    counter = 0
    hostname = RegexedQuestion("Enter an hostname for the interface eth{0}".format(counter),
                               "Hostname must be a string",
                                COMMANDLINELOGGER,
                                "^{0}$".format(hostnameRegex), "").ask()
    ipAddr = RegexedQuestion("Enter an IP address for the interface",
                             "IPAddress must be of form XXX.XXX.XXX.XXX",
                             COMMANDLINELOGGER,
                             "^{0}$".format(ipAddrRegex),"dhcp").ask()
    macAddr = RegexedQuestion("Enter a MAC address for the interface",
                              "MAC address must be of form XX:XX:XX:XX:XX",
                              COMMANDLINELOGGER,
                              "^{0}$".format(macAddrRegex), machination.helpers.generate_random_mac()).ask()
    return (hostname,ipAddr,macAddr)
  
  def requestProvider(self,args,template):
    provider = template.get_providers()[0]
    # If there is more than one provider available for the template
    if len(template.get_providers()) == 1:
      COMMANDLINELOGGER.debug("Template has only one providers. It will be used as the default value")
    else:
      if args.provider != None:
        try:
          provider = Provider.from_string(args.provider)()
        except:
          raise InvalidCmdLineArgument("provider", args.provider)
      else:
        if args.no_interactive == False:
          provider = Provider.from_string(RegexedQuestion("Select a Provider [{0}]".format(",".join(map(str, template.get_providers()))),
                                                         "Provider must be from {0}".format(",".join(map(str, template.get_providers()))),
                                                         COMMANDLINELOGGER,
                                                         "[{0}]".format("\\b|\\b".join(map(str, template.get_providers()))), str(template.get_providers()[0])).ask())()
        else:
          COMMANDLINELOGGER.debug("Missing provider argument")
          raise InvalidCmdLineArgument("provider", args.provider)
    return provider

  def requestProvisionner(self,args,template):
    provisioner = template.get_provisioners()[0]
    # If there is more than one provisioner available for the template
    if len(template.get_provisioners()) == 1:
      COMMANDLINELOGGER.debug("Template has only one provisioner. It will be used as the default value")
    else:
      if args.provisioner != None:
        COMMANDLINELOGGER.debug("A provisioner has been given by the user.")
        try:
          provisioner = Provisioner.from_string(args.provisioner)()
        except:
          COMMANDLINELOGGER.debug("Given provisioner is not supported by machination.")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
        if provisioner not in template.get_provisioners():
          COMMANDLINELOGGER.debug("Given provisioner is not supported by this template.")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
      else:
        if args.no_interactive == False:
          COMMANDLINELOGGER.debug("Request a provisioner to the user.")
          provisioner = Provisioner.from_string(RegexedQuestion("Select an Provisioner [{0}]".format(",".join(map(str, template.get_provisioners()))),
                                                             "Provisioner must be from {0}".format(",".join(map(str, template.get_provisioners()))),
                                                             COMMANDLINELOGGER,
                                                             "[{0}]".format("\\b|\\b".join(map(str, template.get_provisioners()))),
                                                              provisioner.name).ask())()
        else:
          COMMANDLINELOGGER.debug("Missing provisioner argument")
          raise InvalidCmdLineArgument("provisioner", args.provisioner)
              
    return provisioner

  def request_operating_system(self,args,template):
    # If there is more than one OS version available for the template
    # Ask the user to choose
    
    operating_system_name = None
    operating_systems_names = set(operating_system.get_name() for operating_system in template.get_operating_systems())
    if args.operatingsystem != None:
        operating_system_name = args.operatingsystem
        COMMANDLINELOGGER.debug("An operating system has been given by the user.")
    else:
        operating_system_name = next(iter(operating_systems_names))
        if(len(operating_systems_names) > 1):
          COMMANDLINELOGGER.debug("Request a base system to the user.")
          operating_system_name = RegexedQuestion("Select an operating system [{0}]".format(",".join((str(x) for x in operating_systems_names))),
                                      "Operating system must be from {0}".format(",".join((str(x) for x in operating_systems_names))),
                                      COMMANDLINELOGGER,
                                        "[{0}]".format("\\b|\\b".join((str(x) for x in operating_systems_names))), operating_system_name).ask()
        else:
          COMMANDLINELOGGER.debug("Template has only one os version. It will be used as the default value")

    operating_system_architectures = set()
    for operating_system in template.get_operating_systems():
        if operating_system.get_name() == operating_system_name:
          operating_system_architectures.add(operating_system.get_architecture())

    if args.architecture != None:
      COMMANDLINELOGGER.debug("An architecture has been given in by the user.")
      try:
        architecture = Architecture.from_string(self.args.architecture)
        if architecture not in operating_system_architectures:
              COMMANDLINELOGGER.debug("Given architecture is not supported by the template (shall be one of %s).".format(', '.join(operating_system_architectures)))
              raise InvalidCmdLineArgument("architecture", self.args.architecture)
      except:
        COMMANDLINELOGGER.debug("Given architecture is not supported by machination.")
        raise InvalidCmdLineArgument("architecture", self.args.architecture)
    else:
      if len(operating_system_architectures) > 1 :
            if args.no_interactive == False: 
              COMMANDLINELOGGER.debug("Request an architecture...")
              architecture = Architecture.from_string(RegexedQuestion("Select an architecture [{0}]".format(",".join((str(x) for x in operating_system_architectures))),
                                                           "Architecture must be from {0}".format(",".join((str(x) for x in operating_system_architectures))),
                                                           COMMANDLINELOGGER,
                                                           "^[{0}]$".format("\\b|\\b".join((str(x) for x in operating_system_architectures))), architecture.name).ask())
            else:
              COMMANDLINELOGGER.debug("Missing architecture argument")
              raise InvalidCmdLineArgument("architecture", args.architecture)
      else:
          architecture = next(iter(operating_system_architectures))
          COMMANDLINELOGGER.info("Architecture {} will be used as it is the \
  only one supported by system {}".format(architecture, operating_system_name))
    return OperatingSystem(operating_system_name, architecture)
      
  def execute(self,args,templates):
    # Check if the requested template exists
    COMMANDLINELOGGER.debug("Instance '{0}' does not exist, proceeding to its creation.".format(args.name))
    args.template = args.template.replace("\\",'')
    
    template = None
    guestInterfaces = []
    sharedFolders = []
    hostInterface = None
    networkInterfaces = get_all_net_interfaces();
    operating_system = None
    provisioner = None
    provider = None
      
    if args.template in templates.keys():
      template = templates[args.template]
      guestInterfaces = []
      sharedFolders = []
      hostInterface = None
      networkInterfaces = get_all_net_interfaces();
      
      hostInterface = None
      if len(networkInterfaces) == 0:
        COMMANDLINELOGGER.debug("No ethernet interfaces has been found on the host.")
        raise InvalidHardwareSupport("Your host does not have any network interface. Machines cannot be executed")
      else:
        COMMANDLINELOGGER.debug("{0} interfaces has been found on the host: {1}.".format(len(networkInterfaces),', '.join(networkInterfaces)))
        hostInterface = RegexedQuestion("Enter the host interface on which the guest interfaces will be bridged [{0}]".format(",".join(map(str, networkInterfaces))),
                                    "Host interfaces must be from {0}".format(",".join(map(str, networkInterfaces))),
                                    COMMANDLINELOGGER,
                                    "^{0}$".format("\\b|\\b".join(map(str, networkInterfaces))), networkInterfaces[0]).ask()
    
      operating_system = self.request_operating_system(args,template)
      provisioner = self.requestProvisionner(args,template)
      provider = self.requestProvider(args,template) 
        
      # Ask for configuration of network interface of the template
      itfCounter = 0
      if args.guestinterface != None:
        for i in range(0,template.get_guest_interfaces()):
          (ipAddr,macAddr,hostname) = self.unpackInterface(args.guestinterface[itfCounter] )
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
        for i in range(itfCounter, len(args.guestinterface)):
          (ipAddr,macAddr,hostname) = self.unpackInterface(args.guestinterface[itfCounter] )
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr,hostname))
          itfCounter += 1
      else:
        for i in range(0,template.get_guest_interfaces()):
          (ipAddr,macAddr,hostname) = self.requestInterface(networkInterfaces)
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))

      # Ask for additional network interfaces
      if args.no_interactive == False:
        for i in range(itfCounter,template.get_guest_interfaces()):
          (ipAddr,macAddr,hostname) = self.requestInterface(networkInterfaces)
          guestInterfaces.append(NetworkInterface(ipAddr, macAddr, hostname))
      else:
        if(len(args.guestinterface) < template.get_guest_interfaces()):
          COMMANDLINELOGGER.error("Not enough guestinterfaces given to fill requirement of template")
          raise InvalidCmdLineArgument("guestinterface", args.guestinterface)
      if args.no_interactive == False:
        # Ask for adding a new shared folder
        while BinaryQuestion("Do you want to add a shared folder ?",
                           "Enter a Y or a N", COMMANDLINELOGGER, "N").ask():
          hostPathQues = PathQuestion("Enter a path to an existing folder on the host",
                                    "Entered path is invalid, Please enter a valid path",
                                    COMMANDLINELOGGER,
                                    ".+", None, True).ask()
          guestPathQues = PathQuestion("Enter the mount path on the guest directory: ",
                                     "Entered path is invalid, Please enter a valid path",
                                     COMMANDLINELOGGER,
                                     "^/.+", None, False).ask()
          sharedFolders.append(SharedFolder(hostPathQues, guestPathQues))

        if args.sharedfolder != None:
          for s in args.sharedfolder:
            sharedFolders.append(SharedFolder(s[0], s[1]))
        
    else:
      COMMANDLINELOGGER.error("Unable to create machine: template '{0}' does not exists".format(args.template))

      
    return (template, operating_system, provider, provisioner, guestInterfaces, hostInterface, sharedFolders) 
