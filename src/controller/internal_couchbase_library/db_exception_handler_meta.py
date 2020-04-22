#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

import types
import sys
import re
import logging

from plugin_internal_exceptions.couchbase_exception import BucketOperationError, FailedToRunTheCommand, \
    CouchbaseReplicationProfileError, CouchbaseInternalServerError
from plugin_internal_exceptions.couchbase_exception import CouchbaseConnectionError
from plugin_internal_exceptions.couchbase_exception import CouchbaseOperationError
from plugin_internal_exceptions.couchbase_exception import CouchbaseCredentialError
from plugin_internal_exceptions.couchbase_exception import FailedToReadBucketDataFromSnapshot
from plugin_internal_exceptions.base_exception import Response
from controller import helper_lib

logger = logging.getLogger(__name__)

# String literals to match and throw particular type of exceptions.
BUCKET_LIST_EMPTY = "bucket list empty"
UNABLE_TO_CONNECT = "Unable to connect to host at"
UNRECOGNIZED_ARGS = "unrecognized arguments"
CLUSTER_ALREADY_PRESENT = "Cluster reference to the same cluster already exists under the name"
BUCKET_NAME_ALREADY_EXIST = "Bucket with given name already exists"
INCORRECT_CREDENTIAL = "please check your username"
INVALID_BUCKET = "Bucket not found"
ALREADY_CLUSTER_INIT = "Cluster is already initialized, use setting-cluster to change settings"
INVALID_KEY = "object has no attribute"
REPLICATION_ALREADY_PRESENT = "Replication to the same remote cluster and bucket already exists"
DUPLICATE_CLUSTER_NAME = "Duplicate cluster names are not allowed"
MULTIPLE_VDB_ERROR = "Changing data of nodes that are part of provisioned cluster is not supported"
INTERNAL_SERVER_ERROR = "Internal server error, please retry your request"
INTERNAL_SERVER_ERROR1 = "Unable to connect to host"
#Define by us to find the problem
XDCR_OPERATION_ERROR = "Replication Error"
COMMAND_NOT_FOUND = "command not found"
DATA_PATH_ERROR = "An absolute path is required for"
CB_BACKUP_MANGER_FAILED = "Error restoring cluster: Bucket Backup"
SHUTDOWN_FAILED = "shutdown failed"
SERVICE_UNAVAILABLE_ERROR = "is not available on target"
UNEXPECTED_ERROR1 = "Running this command will totally PURGE database data from disk. Do you really want to do"
INVALID_BACKUP_DIR = "Archive directory .* doesn't exist"
BUILD_IN_PROGRESS ="Build Already In Progress"
# This is meta class which decorates the each instance functions with exception handling.
# No need to handle common part in each function of class.
class DatabaseExceptionHandlerMeta(type):

    def __new__(cls, caller_name, caller_base_name, attributes_in_caller):
        """
        :param caller_name:
        :type caller_name: Class type
        :param caller_base_name:
        :type caller_base_name: Any base class of caller_name
        :param attributes_in_caller:
        :type attributes_in_caller: functions and parameters of class
        :return:
        """

        # iteration for each method of a caller class
        for attribute_name, attribute_value in attributes_in_caller.iteritems():
            if isinstance(attribute_value, types.FunctionType):
                if attribute_name == "__init__" or attribute_name == "status":
                    continue
                attributes_in_caller[attribute_name] = cls.handle_exception_decorator(attribute_value)
        try:
            return super(DatabaseExceptionHandlerMeta, cls).__new__(cls, caller_name, caller_base_name,
                                                                    attributes_in_caller)
        except Exception as err:
            logger.debug("Exception occurred while decorating the functions: {}".format(err.message))
            raise Exception

    @classmethod
    def _exception_generator_factory(cls, error_string):
        """
        :param error_string:
        :raises: Exceptions based on the output. It matches the error string with predefined strings.
               In some cases we need to kill the program and in some cases it is not. This is distinguished by the
               error string.
        """
        error_response = Response()
        error_response.std_output = error_string

        if (re.search(CLUSTER_ALREADY_PRESENT, error_string) or
                re.search(BUCKET_NAME_ALREADY_EXIST, error_string) or
                re.search(MULTIPLE_VDB_ERROR, error_string) or
                re.search(SHUTDOWN_FAILED, error_string) or
                re.search(BUILD_IN_PROGRESS, error_string)or
                re.search(ALREADY_CLUSTER_INIT, error_string)):
            logger.debug("Gracefully accepted the last exception")
            return

        if re.search(BUCKET_LIST_EMPTY, error_string):
            error_response.possible_actions = "Bucket list is empty. Please verify if the bucket exist at source"
            error_response.message = "Please check configurations and try again"
        elif re.search(UNABLE_TO_CONNECT, error_string):
            error_response.possible_actions = "Please verify the defined configurations and try again"
            error_response.message = "Internal server error, unable to connect"
        elif re.search(UNRECOGNIZED_ARGS, error_string):
            error_response.message = "Argument(s) mismatch. Please check logs for more details"
            error_response.possible_actions = "Please provide correct configuration details and try again"
        elif re.search(INCORRECT_CREDENTIAL, error_string):
            error_response.message = "Invalid credentials"
            error_response.possible_actions = "Try again with correct credentials"
        elif re.search(REPLICATION_ALREADY_PRESENT, error_string):
            error_response.message = "Duplicate cluster name found"
            error_response.possible_actions = "Delete existing staging cluster configuration on source or use different staging cluster name"
        elif re.search(DUPLICATE_CLUSTER_NAME, error_string):
            error_response.message = "Duplicate cluster name found"
            error_response.possible_actions = "Delete existing staging cluster configuration on source or use different staging cluster name"
        elif re.search(XDCR_OPERATION_ERROR, error_string):
            error_response.message = "Unable to set up XDCR"
            error_response.possible_actions = "Please correct parameters and try again"
        elif (re.search(INTERNAL_SERVER_ERROR, error_string)or
             re.search(INTERNAL_SERVER_ERROR1, error_string)):
            error_response.possible_actions = "Please verify the defined configurations and try again"
            error_response.message = "Internal server error, unable to connect"
        elif re.search(CB_BACKUP_MANGER_FAILED, error_string):
            error_response.possible_actions = "Please verify the provided archive path and try again"
            error_response.message = "Unable to restore backup"
        elif (re.search(SERVICE_UNAVAILABLE_ERROR, error_string) or
             re.search(UNEXPECTED_ERROR1,error_string) ) :
            error_response.possible_actions = "Please try again "
            error_response.message = "Unable to restore backup"
        elif re.search(INVALID_BACKUP_DIR, error_string) :
            error_response.possible_actions = "Try again with correct archive location. "
            error_response.message = "Unable to restore backup"
        else:
            error_response.possible_actions = "Please check logs for more details"
            error_response.message = "Internal error "
        raise Exception(error_response)


    @classmethod
    def handle_exception_decorator(cls, function_name):
        """
        Decorating function with exception handling. Also we can control the output of each couchbase
        command at single place.
        :param function_name: Method of a class which is not static and class
        :type : function
        :return : None
         """

        def wrapper_function(*args, **kwargs):
            #Getting the caller function name
            operation = sys._getframe().f_back.f_code.co_name
            try:
                method_name =  function_name.__name__
                helper_lib.heading("\n########################################################################### Operation : " + method_name.upper() + "  #################################################################################")
                #output_list is array of [output, error ,exit_code ]
                output_list = function_name(*args, **kwargs)
                if helper_lib.is_debug_enabled():
                    if type(output_list) == list and len(output_list) > 0:
                        helper_lib.print_output(output_list[0])
                    elif output_list is not None and type(output_list) is str:
                        helper_lib.print_output(output_list)
                # helper_lib.print_last_line(method_name)
                return output_list
            except Exception as error:
                # error_string = error.message + ", operation:{}".format(operation)
                helper_lib.print_exception(" Found Exception : {}".format(error.message))
                cls._exception_generator_factory(error.message)

        return wrapper_function
