import os
import sys
from waflib.Task import Task

top = "."
out = "build"
src = "src"
     
def options(ctx):
	ctx.add_option('--prefix', action='store', default="/usr/local", help='install prefix')

def configure(ctx):
	ctx.env.PREFIX = ctx.options.prefix
	
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
	confCreationTask = createConfigurationFiles(env=ctx.env)
	confCreationTask.set_outputs(ctx.path.find_dir(out))
	#confCreationTask.set_outputs(ctx.path.find_dir(os.path.join(out,"etc","ansibleCfgFile")))
	ctx.add_to_group(confCreationTask)
	
	sharePath = ctx.path.find_dir('src/share/')
	configPath = ctx.path.find_dir('build/etc/')
	ctx.install_files(os.path.join(ctx.env.PREFIX,'share'), sharePath.ant_glob('**/*'), cwd=sharePath, relative_trick=True)
	ctx.install_files(os.path.join(ctx.env.PREFIX,'etc'),  configPath.ant_glob('**/*'), cwd=configPath, relative_trick=True)

	