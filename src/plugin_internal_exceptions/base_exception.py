#
# Copyright (c) 2020 by Delphix. All rights reserved.
#


from dlpx.virtualization.libs import exceptions

# We are defining two base classes for two types of exceptions: one is related to database & other one is for
# run time errors in plugin. Both classes are child class of PluginScriptError which is defined by the VSDK lib
# Purpose of segregation of these two kind of exceptions is to get more accurate message at runtime error/exceptions.

# All the exceptions created for database will inherit the DatabaseException and these are defined in current directory
# with name couchbase_exceptions.py. Catching and Raising the db exceptions are maintained by controller package.
class DatabaseException(exceptions.PluginScriptError):
    def __init__(self, message):
        super(DatabaseException, self).__init__(message)



# Exceptions related to plugin operation like discovery, linking, virtualization are being handled using this.
# plugin_exception.py is responsible to catch and throw specific error message for each kind of delphix operation.
class PluginException(exceptions.PluginScriptError):
    def __init__(self, message):
        super(PluginException, self).__init__(message)



class Response(Exception):
    def __init__(self, std_output=None, user_message=None, possible_actions=None):
        self.std_output = std_output
        self.user_message = user_message
        self.possible_actions = possible_actions