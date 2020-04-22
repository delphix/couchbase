#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

import logging
import re

from dlpx.virtualization import libs
from db_commands_data import cbase_command
from dlpx.virtualization.libs import exceptions
from plugin_internal_exceptions.base_exception import Response


# logger object
logger = logging.getLogger(__name__)

def execute_bash(source_connection, command_name, callback_func=None, **kwargs ):
    """

    :param source_connection: Connection object for the source environment
    :param command_name: Command to be search from dictionary of bash command
    :param kwargs: Dictionary to hold key-value pair for this command
    :return: list of output of command, error string, exit code
    """

    if type(kwargs) != dict :
        raise exceptions.PluginScriptError("Parameters should be type of dictionary")

    if(source_connection is None):
        raise exceptions.PluginScriptError("Connection object cannot be empty")
    command = command_builder(command_name, **kwargs)


    # Putting if block because in some cases, environment_vars is not defined in kwargs then we need to pass empty
    # dict. Otherwise it will raise Exception.
    if 'environment_vars' in kwargs.keys():
        environment_vars = kwargs['environment_vars']
        if type(environment_vars) != dict:
            raise exceptions.PluginScriptError("environment_vars should be type of dictionary. Current type is{}".format(type(environment_vars)))
    else:
        #making empty environment_variable for this command
        environment_vars = {}
    result = libs.run_bash(source_connection, command=command, variables=environment_vars, use_login_shell=True)

    # strip the each part of result to remove spaces from beginning and last of output
    output = result.stdout.strip()
    error = result.stderr.strip()
    exit_code = result.exit_code

    if exit_code != 0:
        logger.debug("Executed command is \n{}\n\n".format(" ".join(command.split())))

    # Verify the exit code of each executed command. 0 means command ran successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will die and otherwise execution will continue.
    _handle_exit_code(exit_code, error, output, callback_func)
    return [output, error ,exit_code ]


def command_builder(command_name, **kwargs):
    """

    :param command_name: It specify the command name to search from cbase_command.py
    :param kwargs: required parameters for this command
    :return:  command with parameters
    """
    return cbase_command.data.commands[command_name].format(**kwargs)


def _handle_exit_code(exit_code, std_err=None, std_output=None, callback_func=None):

    if (exit_code == 0):
        return

    else:
        #Call back function which contains logic to skip the error and continue to throw
        if (callback_func != None):
            logger.debug("Executing call back. Seems some exception is observed. Validating last error...")
            try:
                result_of_match = callback_func(std_output)
                logger.debug("Call back result is : {}".format(result_of_match))
                if result_of_match == True :
                    return True
            except Exception as err:
                logger.debug("Failed to execute call back function with error: {}".format(err.message))

    #Raising exception
    logger.debug(" exit_Code:{}, std_err:{},  std_output:{}".format(exit_code, std_err , std_output))

    error_details = std_output
    if error_details == None or error_details== "":
        error_details = std_err
    #TODO Check if we can create response object here itself
    raise Exception(error_details)
    # raise Exception("exit_Code:{}, std_err:{},  std_output:{}".format(str(exit_code), str(std_err), str(std_output)))


