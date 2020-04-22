#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

# This module is defined to provide common functionality which is being used across this plugin.
# Like some calculation, log some heading and also operations required in discovery

import os
import os.path
import json
import logging
import random
import re
import time
from datetime import datetime

from dlpx.virtualization.libs import exceptions
from plugin_internal_exceptions.plugin_exception import RepositoryDiscoveryError, SourceConfigDiscoveryError
from plugin_internal_exceptions.couchbase_exception import BucketOperationError
from utils import utilities


# Not Defined parameters
BucketNameIsNotDefined = None
RamSizeIsNotDefined = None
FlushValueIsNotDefined = None
SourceConfigIsNotDefined =None

# Constants
StatusIsActive="healthy"
DELPHIX_HIDDEN_FOLDER = ".delphix"
CONFIG_FILE_NAME = "config.txt"

# This class helps logging in colorful manner. So whenever we see the plugin logs in tail command then easy to segregate
# the command/output/exception/completion message
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Global logger object for this file
logger = logging.getLogger(__name__)


def find_binary_path(source_connection):
    logger.debug("Finding Binary Path...")
    binary_paths, std_err, exit_code = utilities.execute_bash(source_connection, command_name='find_binary_path')
    if binary_paths == "":
        logger.warn("Please check environment variable COUCHBASE_PATH is defined. Checking in default location")
        binary_paths = "/opt/couchbase/bin"
    else:
        logger.debug("List of couchbase path found are {}".format(binary_paths.split(';')))
    logger.debug("Finding Binary: {}".format(binary_paths))
    return binary_paths


def find_shell_path(source_connection, binary_path):
    logger.debug("Finding Shell Path...")
    env = {}
    env['binary_path'] = binary_path
    shell_path, std_err, exit_code = utilities.execute_bash(source_connection, command_name='find_shell_path', **env)
    if (shell_path == ""):
        message = u"exit_Code:1, std_err:Shell path {}/couchbase-cli not found,  std_output:, command:find_install_path".format(
            binary_path)
        logger.error(message)
        raise RepositoryDiscoveryError(message)
    return shell_path

def find_install_path(source_connection, binary_path):
    logger.debug("Finding install Path...")
    env = {}
    env['binary_path'] = binary_path
    install_path, std_err, exit_code = utilities.execute_bash(source_connection, command_name='find_install_path', **env)
    if (install_path == ""):
        message = u"exit_Code:1, std_err:Install path {}/couchbase-server not found,  std_output:, command:find_install_path".format(binary_path)
        logger.error(message)
        raise RepositoryDiscoveryError(message)
    else:
        logger.debug("couchbase-server found in directory {}".format(install_path))
    return install_path


def find_version(source_connection, install_path):
    raw_version, std_err, exit_code = utilities.execute_bash(source_connection, "get_version",
                                                             install_path=install_path)
    version = re.search(r"\d.*$", raw_version).group()
    logger.debug("Couchbase version installed {}".format(version))
    return version


def is_instance_present_of_gosecrets(source_connection):
    instance, stderr, exit_code = utilities.execute_bash(source_connection,command_name = "get_process")
    #return true if 'gosecrets' string is present in output of get_process
    return "gosecrets" in instance


def get_data_directory(source_connection, repository):
    couchbase_install_path = repository.cb_install_path
    couchbase_binary_path = os.path.dirname(couchbase_install_path)
    couchbase_base_dir = os.path.dirname(couchbase_binary_path)
    filename = "{}/etc/couchbase/static_config".format(couchbase_base_dir)
    static_config,stderr,exit_code = utilities.execute_bash(source_connection, command_name="read_file", filename=filename)
    if not re.search(r"(?<=path_config_datadir, \").*(?=\"}\.)",static_config):
        message = u"exit_Code:1, std_err:Cannot find data directory,  std_output:"
        logger.error(message)
        raise SourceConfigDiscoveryError(message)
    data_directory = re.search(r"(?<=path_config_datadir, \").*(?=\"}\.)",static_config).group()
    return data_directory


# Return the base directory of given path
def get_base_directory_of_given_path(binary_path):
    path = os.path.split(binary_path)[0]
    return path


# Return bucket name with ramsize
def get_all_bucket_list_with_size(bucket_output, bucket=None):
    logger.debug("bucket_output: {}".format(bucket_output))
    additional_buffer = 10
    min_size = 104857600
    all_bucket_list = ""
    for line in bucket_output:
        logger.debug("line: {}".format(line))
        bucket_name = None
        ram_size = 0
        if (line.find(':') == -1):
            all_bucket_list = all_bucket_list + line + ","
        elif (line.find("ramUsed") != -1):
            ram_size = int(line.split(':')[1].strip())
            # Formula used usedbucketsize/2 + 10% additional memory
            ram_size = (ram_size)/2 + ((ram_size/2) * additional_buffer // 100)
            # Always start with minimum size i.e. 100MB. Customer can on the fly increase from GUI. Above calculation is not used.
            # but may be useful for future use cases and enhancements
            # ram_size = min_size
            logger.debug("before ram_size: {}".format(ram_size))
            if (ram_size < min_size):
                ram_size = min_size
            logger.debug("after ram_size: {}".format(ram_size))
            all_bucket_list = all_bucket_list + str(ram_size) + ":"
            logger.debug("all_bucket_list: {}".format(all_bucket_list))
    all_bucket_list = all_bucket_list.strip(":")
    logger.debug("All bucket list is: {}".format(all_bucket_list))
    return all_bucket_list.split(":")


def get_stg_all_bucket_list_with_ramquota_size(bucket_output):
    logger.debug("bucket_output: {}".format(bucket_output))
  
    all_bucket_list = ""
    for line in bucket_output:
        logger.debug("line: {}".format(line))
        bucket_name = None
       
        if (line.find(':') == -1):
            all_bucket_list = all_bucket_list + line + ","
        elif (line.find("ramQuota") != -1):
            ram_quota = int(line.split(':')[1].strip())
            logger.debug("after ram_size: {}".format(ram_quota))
            all_bucket_list = all_bucket_list + str(ram_quota) + ":"
            logger.debug("all_bucket_list: {}".format(all_bucket_list))
    all_bucket_list = all_bucket_list.strip(":")
    logger.debug("All bucket list is: {}".format(all_bucket_list))
    return all_bucket_list.split(":")


# Filter bucket name from command output
def filter_bucket_name_from_output(bucket_output):
    output = filter(lambda bucket: bucket.find(":") == -1, bucket_output)
    logger.debug("Bucket list: {}".format(output))
    return output


def get_bucket_name_with_size(bucket_output, bucket):
    output = get_all_bucket_list_with_size(bucket_output, bucket)
    output = ":".join(output)
    bucket_info = re.search(r"{},\d+".format(bucket),output).group()
    logger.debug("For Bucket {} detail is : {}".format(bucket, bucket_info))
    return bucket_info

# Return only bucket name of given complete output
def get_bucketlist_to_namesize_list(bucket_output, bucket_list):
    bucket_details = []
    for name in bucket_list:
        bucket_details.append(get_bucket_name_with_size(bucket_output, name))
    logger.debug("Buckets: {}  \n details : {}".format(bucket_list, bucket_details))
    return bucket_details

# Sleep/Pause the execution for given seconds
def sleepForSecond(sec):
    # logger.debug("Waiting For {} second|s".format(sec))
    time.sleep(sec)

# Return current time in format of %Y%m%d%H%M%S'
def current_time():
    curr_time = datetime.now()
    return curr_time.strftime('%Y%m%d%H%M%S')

# return the value of key in provided json object
def get_value_of_key_from_json(json_obj, key):
    value =  json.loads(json_obj)[key]
    heading(key + " is :"+ value)
    return value

# Print given data into passed file-path
def write_file(connection, content,filename):
    #Add exception handling here
    logger.debug("writing data {}".format(content))
    utilities.execute_bash(connection, 'write_file', data=content, filename=filename)

# If file is present then it returns true.
def check_file_present(connection, config_file_path):
    logger.debug("Checking file {}".format(config_file_path))
    try:
        stdout, stderr, exit_code = utilities.execute_bash(connection, 'check_file', file_path=config_file_path)
        if(stdout=="Found"):
            logger.debug("file path exist".format(config_file_path))
            return True
    except Exception:
        pass
    logger.debug("File path not exist".format(config_file_path))
    return False

# If folder is present then it returns true.
def check_dir_present(connection, dir):
    logger.debug("checking directory {}".format(dir))
    try:
        stdout, stderr, exit_code = utilities.execute_bash(connection, 'check_directory', dir_path=dir)
        if(stdout=="Found"):
            logger.debug("dir path exist {} ".format(dir))
            return True
    except Exception as error:
        logger.debug("Found error while searching path {}".format(error.message))
    logger.debug("directory path is not exist : {}".format(dir))
    return False

# read the file content and return the output
def read_file(connection, filename):
    logger.debug("Reading file {}".format(filename))
    stdout, stderr, exit_code = utilities.execute_bash(connection, 'read_file', filename=filename)
    return [stdout, stderr, exit_code]

# delete file
def delete_file(connection, filename):
    logger.debug("Deleting file {}".format(filename))
    stdout, stderr, exit_code = utilities.execute_bash(connection, 'delete_file', filename=filename)
    return [stdout, stderr, exit_code]

# To generate the snapshot id each time using random function
def get_snapshot_id():
    return random.randint(100000000,999999999)

# Print 100 hyphens in log
def print_sign(sign="-"):
    size = sign*60
    logger.debug(size)

# Print message in between of two lines of #. It gives clarity what is currently executing
def heading(msg,level='debug'):
    # logger.debug(bcolors.OKBLUE + '#'*83 + bcolors.ENDC)
    if level is 'info':
        logger.info(msg)
    else:
        logger.debug(bcolors.OKBLUE+msg+bcolors.ENDC)
    # logger.debug(bcolors.OKBLUE + '#'*83 + bcolors.ENDC)

# Output of each command will print in this format
def print_output(output):
    logger.debug(bcolors.WARNING + "Command output is - " + bcolors.ENDC)
    logger.debug(bcolors.BOLD + output + bcolors.ENDC)

# Last line of each execution in format
def print_last_line(msg=None):
    logger.debug(bcolors.OKGREEN + "---------Execution Done for '"+ msg+"'-------------\n" + bcolors.ENDC)

# To show the exceptions in red color
def print_exception(msg):
    logger.debug(bcolors.FAIL + msg + bcolors.ENDC)



def end_line():
    print_sign(sign="+")
    logger.debug("\n")

def is_debug_enabled():
    # Add logic to enable the debug mode here
    # To see the vsdk parameters and output of each command
    return False

def unmount_file_system(rx_connection, path):
    try:
        # env = {}
        # env['mount_path'] = mount_path
        stdout, stderr, exit_code = utilities.execute_bash(rx_connection, 'unmount_file_system', mount_path=path)
    except Exception as err:
        logger.debug("error here {}".format(err.message) )


