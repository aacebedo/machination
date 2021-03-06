import os
import sys
from waflib.Task import Task
from waflib import Logs
import subprocess
from distutils.version import LooseVersion, StrictVersion
import imp
import re
import stat
import distutils.spawn

top = "."
out = "build"
src = "src"

def options(ctx):
	ctx.add_option('--prefix', action='store', default="/usr/local", help='install prefix')
	ctx.add_option('--templates', action='store', default="*", help='templates to install')

def checkVersion(name,cmd,regex,requiredVersion,returnCode):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking {0} version'.format(name)),sep=': ')
    try:
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        line=" "
        p.wait()
        lines = list()
        for line in iter(p.stdout.readline,''):
           lines.append(line)
        for line in iter(p.stderr.readline,''):
           lines.append(line)

        res =  { "returncode": p.returncode, "out":lines[0][0:-1] }
        if res["returncode"] != returnCode:
           Logs.pprint('RED','{0} is not available. Cannot continue.'.format(name))
        else:
          v = re.match(regex, res["out"])
          version = v.group(1)
          requiredVersionObj = LooseVersion(requiredVersion)
          currentVersionObj = LooseVersion(version)
          if currentVersionObj >= requiredVersionObj:
              Logs.pprint('GREEN',version)
              res = True
          else:
              Logs.pprint('RED','Incorrect version {0} (must be equal or greater than {1}). Cannot continue.'.format(currentVersionObj,requiredVersionObj))
    except Exception as e:
        Logs.pprint('RED','Unable to get version ({0}).'.format(e))
    return res

def checkBinary(name,*cmds):
    res = False
    for cmd in cmds:
      Logs.pprint('WHITE','{0: <40}'.format('Checking {0}'.format(cmd)),sep=': ')
      try:
        res = distutils.spawn.find_executable(cmd)
        if res is None:
           Logs.pprint('RED','no')
        else:
           Logs.pprint('GREEN',"present")
	   break
      except:
          Logs.pprint('RED','Unable to check binary.')
    if res is False:
      Logs.pprint('RED','{0} is not available. Cannot continue.'.format(name))
    return res

def checkPythonModule(*moduleNames):
    res = False
    for mod in moduleNames:
      Logs.pprint('WHITE','{0: <40}'.format('Checking python module {0}'.format(mod)),sep=': ')
      try:
        imp.find_module(mod)
        res = True
	break
      except ImportError:
        Logs.pprint('RED','no')
        res = False
    if not res:
       Logs.pprint('RED','Required Python module is not available. Cannot continue')
    else :
      Logs.pprint('GREEN',"ok")
      res = True
    return res

def configure(ctx):
    ctx.env.PREFIX = ctx.options.prefix

    if ctx.options.templates == "":
    	ctx.env.TEMPLATES = None
    else:
    	ctx.env.TEMPLATES = ctx.options.templates.split(",")

    if not checkVersion("Python","python --version","Python ([0-9\.]*)","2.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Vagrant","vagrant -v","Vagrant ([0-9\.]*)","1.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Ansible","ansible --version","ansible ([0-9\.]*)","1.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Docker","docker --version","Docker version ([0-9\.]*)(.*)","1.4.1",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkBinary("Dhcp","udhcpc", "dhcpd", "dhclient"):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("packer","packer --version","(.*)([0-9\.]*)(.*)","0.8.1",1):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkPythonModule("enum34", "enum"):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkPythonModule("argcomplete"):
      ctx.fatal("Missing requirements. Installation will not continue.")


def build(ctx):
  sharePath = ctx.path.find_dir('src/share/')
  binPath = ctx.path.find_dir('src/bin/')
  etcPath = ctx.path.find_dir('src/etc/')

  etcFiles = etcPath.ant_glob('**/*',excl="**/machination/templates/*")
  templateFiles = []

  for t in ctx.env.TEMPLATES:
  	templateFiles.extend(etcPath.ant_glob('**/machination/templates/'+t+'.*.template'))


  ctx.install_files(os.path.join(ctx.env.PREFIX,'share'), sharePath.ant_glob('**/*'), cwd=sharePath, relative_trick=True)
  ctx.install_files(os.path.join(ctx.env.PREFIX,'bin'), binPath.ant_glob('**/*'),  chmod=0555, cwd=binPath, relative_trick=True)
  ctx.install_files(os.path.join(ctx.env.PREFIX,'etc'), etcFiles, cwd=etcPath, relative_trick=True)
  ctx.install_files(os.path.join(ctx.env.PREFIX,'etc'), templateFiles, cwd=etcPath, relative_trick=True)
