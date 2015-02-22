import re
import os

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
            self._default = ""
    
    def ask(self):
        questionTmp = self._question
        if self._default != "":
            questionTmp += " [" + self._default + "]"
        v = raw_input(questionTmp+ ": ")
        if v == "":
            v = self._default
        if re.match(self._regex,v) :
            return v
        else:            
            return RegexedQuestion.ask(self)
        
class BinaryQuestion(RegexedQuestion):
    _question = ""
    _options = None
    
    def __init__(self,question,default = None):
        if type(default) is str and re.match("Y|y|N|n",default):
            self._default = default
            
        RegexedQuestion.__init__(self,question+" Y/N","Y|y|N|n",default)
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
    _checkExists = False

    def __init__(self,question,regex = ".?" ,default = None,checkExists = False):
        RegexedQuestion.__init__(self,question,regex,default)
        self._checkExists = checkExists        
        
    def ask(self):
        v = RegexedQuestion.ask(self)
        if (not self._checkExists) or os.path.exists(v) :
            return v
        else:
            return self.ask() 