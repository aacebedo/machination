
class ArgumentValidationError(ValueError):
    '''
    Raised when the type of an argument to a function is not what it should be.
    '''
    def __init__(self, arg_num, func_name, accepted_arg_type):
        self.error = 'The {0} argument of {1}() is not a {2}'.format(arg_num,
                                                                     func_name,
                                                                     accepted_arg_type)
 
    def __str__(self):
        return self.error
 
class InvalidArgumentNumberError(ValueError):
    '''
    Raised when the number of arguments supplied to a function is incorrect.
    Note that this check is only performed from the number of arguments
    specified in the validate_accept() decorator. If the validate_accept()
    call is incorrect, it is possible to have a valid function where this
    will report a false validation.
    '''
    def __init__(self, func_name):
        self.error = 'Invalid number of arguments for {0}()'.format(func_name)
 
    def __str__(self):
        return self.error
 
class InvalidReturnType(ValueError):
    '''
    As the name implies, the return value is the wrong type.
    '''
    def  __init__(self, return_type, func_name):
        self.error = 'Invalid return type {0} for {1}()'.format(return_type,
                                                                func_name)
 
    def __str__(self):
        return self.error

class InvalidArgumentValue(ValueError):
    def __init__(self, argName):
        self.error = 'Invalid value for argument {0}'.format(argName)
            
    def __str__(self):
        return self.error

class PathNotExistError(ValueError):
    def __init__(self, argName):
        self.error = 'Path {0} does not exists'.format(argName)
            
    def __str__(self):
        return self.error
        
class MachineInstanceAlreadyExistsException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)

class MachineInstanceDoNotExistException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)
    
class InvalidMachineTemplateException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)
    
class InvalidMachineInstanceException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)

    
class InvalidYAMLException:
    _message = ""
    def __init__(self, message):
        self._message = message
    
    def __str__(self):
        return repr(self._message)
    