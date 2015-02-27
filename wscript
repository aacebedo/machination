import os
import sys
from waflib.Task import Task
from waflib import Logs
import subprocess
from distutils.version import LooseVersion, StrictVersion
import imp

top = "."
out = "build"
src = "src"
     
def options(ctx):
	ctx.add_option('--prefix', action='store', default="/usr/local", help='install prefix')

def checkPythonModule(moduleName):
  res = False
  try:
      imp.find_module('eggs')
      res = True
  except ImportError:
      res = False
  return res

def checkBinary(cmd):
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE,stdout=subprocess.PIPE)
    line=" "
    p.wait()
    for line in iter(p.stdout.readline,''):
        pass
    return { "returncode": p.returncode, "out":line[0:-1] }
        
def checkVagrant(requiredVersion):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking Vagrant version'),sep=': ')
    res =  checkBinary("vagrant -v")
    if res["returncode"] != 0:
       Logs.pprint('RED','Vagrant is not available. Cannot continue')
    else :
      Logs.pprint('GREEN',res["out"])
      res = True
    return res

def checkDockerVersion(requiredVersion):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking Vagrant version'),sep=': ')
    try:
        res =  checkBinary("vagrant -v")
        if res["returncode"] != 0:
           Logs.pprint('RED','Vagrant is not available. Cannot continue')  
        else:
          requiredVersionObj = StrictVersion(requiredVersion)
          currentVersionObj = StrictVersion(out.split(" ")[2])
          if currentVersionObj >= requiredVersionObj:
              Logs.pprint('GREEN',res["out"])
              res = True
          else:
              Logs.pprint('RED','Incorrect version {0} (must be equal or greater than {1}). Cannot continue.'.format(currentVersionObj,requiredVersionObj))
    except:
        Logs.pprint('RED','Unable to get version.')
    return res

def checkAnsible(requiredVersion):
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Getting Ansible version'),sep=': ')
    res =  checkBinary("ansible2 --version")
    if res["returncode"] != 0:
       Logs.pprint('RED','Ansible is not available. Cannot continue')
    else :
      Logs.pprint('GREEN',res["out"])
      res = True
    return res
  
def checkEnumPython():
    res = False
    Logs.pprint('WHITE','{0: <40}'.format('Checking enum extension for Python'),sep=': ')
    res =  checkPython("enum")
    if not res:
       Logs.pprint('RED','Enum python extension is not available. Cannot continue')
    else :
      Logs.pprint('GREEN',res["out"])
      res = True
    return res
           
           
def configure(ctx):
    ctx.env.PREFIX = ctx.options.prefix
    if not checkVagrant():
      ctx.fatal("Missing requirements. Installation will not continue.")
    if not checkAnsible():
	  ctx.fatal("Missing requirements. Installation will not continue.")
	
class createConfigurationFiles(Task):
	def run(self):
		configDir = os.path.join('etc','machination')
		filePath = os.path.join('etc','machination','ansible.cfg')
		d = os.path.join(self.outputs[0].abspath(),configDir)
	 	if not os.path.exists(d):
	 		os.makedirs(d)
		ansibleCfgFile = open(os.path.join(self.outputs[0].abspath(),filePath),"w")
		print >> ansibleCfgFile,  '[defaults]'
		print >> ansibleCfgFile, 'roles_path=',os.path.abspath(os.path.join(self.env.PREFIX,'share','machination','provisioners','ansible','roles')),':~/.machination/providers/ansible/roles'
		ansibleCfgFile.close()
		self.outputs.append(self.outputs[0].find_or_declare(filePath))
				
def build(ctx):
	#confCreationTask = createConfigurationFiles(env=ctx.env)
	#confCreationTask.set_outputs(ctx.path.find_dir(out))
	#confCreationTask.set_outputs(ctx.path.find_dir(os.path.join(out,"etc","ansibleCfgFile")))
	#ctx.add_to_group(confCreationTask)
	
	sharePath = ctx.path.find_dir('src/share/')
	sharePath = ctx.path.find_dir('src/bin/')
    
    #configPath = ctx.path.find_dir('build/etc/')
	ctx.install_files(os.path.join(ctx.env.PREFIX,'share'), sharePath.ant_glob('**/*'), cwd=sharePath, relative_trick=True)
	ctx.install_files(os.path.join(ctx.env.PREFIX,'bin'), binPath.ant_glob('**/*'), cwd=binPath, relative_trick=True)
    
    #ctx.install_files(os.path.join(ctx.env.PREFIX,'etc'),  configPath.ant_glob('**/*'), cwd=configPath, relative_trick=True)

	