#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
import re
import logging
from base_exception import PluginException, Response
from dlpx.virtualization.libs import exceptions
from dlpx.virtualization.platform.exceptions import UserError
logger = logging.getLogger(__name__)


# Decorator to add exception handling for the functions defined in modules of operations package
def handle_plugin_exception(exception_name):
    def exception_decorator(function):
        def wrapper_function(*args, **kwargs):
            try:
                result = function(*args, **kwargs)
                return result
            except Exception as error:
                exception_generator(error, exception_name)
        return wrapper_function
    return exception_decorator

# Identify the operation name from error message and raise the particular exception
# Operation parameter is being set in db_exception_handler_meta class
def exception_generator(error, exception_name):
    logger.debug("Error is {} \n exception_name is {}".format(error, exception_name))
    stderr, exit_code, operation, stdout= None, None, None, None
    try:
        stdout = error
        if(error.message != ""):
            stdout = re.search(r"(?<=std_output:).*(?=,)", error).group()
    except Exception:
        logger.debug("Failed to find stdout")
    # try:
    #     stderr = re.search(r"(?<=std_err:).*(?=, {2})", error.message).group()
    # except Exception as err:
    #     logger.debug("Failed to find stderr")

    # try:
    #     operation = re.search(r"(?<=operation:).*", error.message).group()
    # except Exception as err:
    #     logger.debug("Failed to find operation")

    # try:
    #     exit_code = int(re.search(r"(?<=exit_Code:)[0-9]*(?=,)", error.message).group())
    # except Exception as err:
    #     logger.debug("Failed to find exit_code")

    # if stderr == None or stderr == "":
    #     Error = " Error could be : "
    #     if stdout != None or stdout !="":
    #         Error = Error + str(stdout)
    #     elif error.message != None:
    #         Error = Error + str(error.message)
    #     stderr = "Database exception: "+str(type(error)) + str(Error)
    # else:
    #     stderr = "Database exception: "+str(type(error)) + "\n with error message: " + str(stderr)
    logger.debug("stderr is ".format(stderr))
    raise UserError("", "",stdout)


def handle_error_response(error, append_msg=" "):
    if(error):
        if type(error.message) is Response:
            response = error.message
            raise UserError(append_msg + str(response.message), response.possible_actions, response.std_output)
        if type(error) is Response :
            raise UserError(append_msg + str(error.message), error.possible_actions, error.std_output)
        if hasattr(error, 'message'):
            raise UserError(append_msg, "", error.message)
        else:
            raise UserError(append_msg, "", error)
    raise UserError(append_msg, "", error)

class ScriptError(PluginException):
    def __init__(self, message):
        super(ScriptError, self).__init__(message)

class InvalidOperation(PluginException):
    def __init__(self, message):
        super(InvalidOperation, self).__init__(message)



#This exception will be raised when failed to Discovery the repository
class RepositoryDiscoveryError(PluginException):
    def __init__(self, message):
        super(RepositoryDiscoveryError, self).__init__(message)



#This exception will be raised when failed to find source config
class SourceConfigDiscoveryError(PluginException):
    def __init__(self, message):
        super(SourceConfigDiscoveryError, self).__init__(message)




class DuplicateKeyError(PluginException):
    def __init__(self, message):
        super(DuplicateKeyError, self).__init__(message)



#This exception will be raised When Resync operation is failed
class ResyncFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(ResyncFailedError, self).__init__(message)



#This exception will be raised When Enable operation is failed
class EnableFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(EnableFailedError, self).__init__(message)



#This exception will be raised when Disable is failed
class DisableFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(DisableFailedError, self).__init__(message)



#This exception will be raised when failed to get status of vdb/dsource
class StatusFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(StatusFailedError, self).__init__(message)



#This exception will be raised when provisioning is failed
class ProvisionFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(ProvisionFailedError, self).__init__(message)



#This exception will be raised when vdb refresh is failed
class RefreshFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(RefreshFailedError, self).__init__(message)



#This exception will be raised when vdb start is failed
class VDBStartFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(VDBStartFailedError, self).__init__(message)



#This exception will be raised when DB stop failed
class VDBStopFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(VDBStopFailedError, self).__init__(message)



#This exception will be raised when post snap shot is failed
class PostSnapshotFailedError(exceptions.PluginScriptError):
    def __init__(self, message):
        super(PostSnapshotFailedError, self).__init__(message)
