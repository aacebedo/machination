import random
import os
import errno
import re

def listPath(d):
    if(os.path.exists(d)):
        return [os.path.join(d, f) for f in os.listdir(d)]
    else:
        return []
    
def randomMAC():
    mac = [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))
    
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

class RegexedQuestion:
    _question = ""
    _regex = ""
    _options = []
    _default = None
    
    def __init__(self,question,regex = ".*", default = None):
        self._question = question
        self._regex = regex
        if type(default) is str:
            self._default = default
        else:
            self.default = ""
    
    def ask(self):
        questionTmp = self._question
        if self._default != None:
            questionTmp += " [" + self._default + "]"
        v = raw_input(questionTmp+ ": ")
        if v == "":
            v = self._default        
        if not re.match(self._regex,v) :
            return RegexedQuestion.ask(self)
        else:            
            return v
        
class BinaryQuestion(RegexedQuestion):
    _question = ""
    _options = None
    
    def __init__(self,question,default = None):
        if type(default) is str and re.match("[Y,N]",default):
            self.default = default
            
        RegexedQuestion.__init__(self,question+" {Y/N}","[Y,y,N,n]",default)
        self._options = {
                         "Y" : self.ok,
                         "y" : self.ok,
                         "N" : self.nok,
                         "n" : self.nok
                         }
    
    def ok(self):
        return True
    
    def nok(self):
        return False
    
    def ask(self):
        v = RegexedQuestion.ask(self)
        return (self._options.get(v))()
    
class PathQuestion(RegexedQuestion):
    _question = ""
    _regex = ""
    _checkExists = False
    _options = []
    
    def __init__(self,question,regex = ".*" ,default = "",checkExists = False):
        questionTmp = self._question
        if default != "":
            questionTmp += "[" + self._default + "}"
        RegexedQuestion.__init__(questionTmp,regex)
        self._checkExists = checkExists        
        self._default = default
    
    def ask(self):
        v = super(RegexedQuestion, self).ask()
        if (not self._checkExists) or os.path.exists(v) :
            return v
        else:
            return self.ask() 
    
    
def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result