import os
import sys
from waflib.Task import Task
from waflib import Logs
import subprocess
from distutils.version import LooseVersion, StrictVersion
import imp
import re
import stat
top = "."
out = "build"
src = "src"

def options(ctx):
	ctx.add_option('--prefix', action='store', default="/usr/local", help='install prefix')

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

def checkBinary(name,cmd,returnCode):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking {0} version'.format(name)),sep=': ')
    try:
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        line=" "
        p.wait()
        for line in iter(p.stdout.readline,''):
           pass
        for line in iter(p.stderr.readline,''):
           pass
        res =  { "returncode": p.returncode, "out":line[0:-1] }
        if res["returncode"] != returnCode:
           Logs.pprint('RED','{0} is not available. Cannot continue.'.format(name))
        else:
           Logs.pprint('GREEN',"present")
    except:
        Logs.pprint('RED','Unable to check binary.')
    return res

def checkPythonModule(moduleName):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking python module {0}'.format(moduleName)),sep=': ')
    try:
      imp.find_module(moduleName)
      res = True
    except ImportError:
      res = False
    if not res:
       Logs.pprint('RED','{0} python module is not available. Cannot continue')
    else :
      Logs.pprint('GREEN',"ok")
      res = True
    return res

def configure(ctx):
    ctx.env.PREFIX = ctx.options.prefix
    if not checkVersion("Python","python --version","Python ([0-9\.]*)","2.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Vagrant","vagrant -v","Vagrant ([0-9\.]*)","1.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Ansible","ansible --version","ansible ([0-9\.]*)","1.7.0",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkVersion("Docker","docker --version","Docker version ([0-9\.]*)(.*)","1.4.1",0):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkBinary("Udhcpc","udhcpc --help",1):
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkPythonModule("enum"):
      ctx.fatal("Missing requirements. Installation will not continue.")

def build(ctx):
  sharePath = ctx.path.find_dir('src/share/')
  binPath = ctx.path.find_dir('src/bin/')
  etcPath = ctx.path.find_dir('src/etc/')

  ctx.install_files(os.path.join(ctx.env.PREFIX,'share'), sharePath.ant_glob('**/*'), cwd=sharePath, relative_trick=True)
  ctx.install_files(os.path.join(ctx.env.PREFIX,'bin'), binPath.ant_glob('**/*'),  chmod=0555, cwd=binPath, relative_trick=True)
  ctx.install_files(os.path.join(ctx.env.PREFIX,'etc'), etcPath.ant_glob('**/*'), cwd=binPath, relative_trick=True)
