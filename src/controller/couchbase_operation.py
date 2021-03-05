#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
This class defines methods for couchbase operations. Parent classes are: _BucketMixin, _ClusterMixin, _ReplicationMixin,
 _XDCrMixin, _CBBackupMixin. Modules name is explaining about the operations for which module is created for.
The constructor of this class expects a `builder` on which each database operation will be performed
Commands are defined for each method in module commands.py. To perform any delphix operation we need to create
the object of this class. This class is single connector between other modules and `controller` package.
"""
#######################################################################################################################

import re
import logging
import os
import sys
import json

from dlpx.virtualization.platform import Status

from internal_exceptions.database_exceptions import CouchbaseServicesError
from utils import utilities
from controller.resource_builder import Resource
from controller import helper_lib
from controller.couchbase_lib._bucket import _BucketMixin
from controller.couchbase_lib._cluster import _ClusterMixin
from controller.couchbase_lib._replication import _ReplicationMixin
from controller.couchbase_lib._xdcr import _XDCrMixin
from controller.couchbase_lib._cb_backup import _CBBackupMixin
from db_commands.commands import CommandFactory
from db_commands.constants import ENV_VAR_KEY, StatusIsActive, DELPHIX_HIDDEN_FOLDER, CONFIG_FILE_NAME
from controller.helper_lib import remap_bucket_json
import time

logger = logging.getLogger(__name__)


class CouchbaseOperation(_BucketMixin, _ClusterMixin, _ReplicationMixin, _XDCrMixin, _CBBackupMixin):

    def __init__(self, builder):
        """
        Main class through which other modules can run databases operations on provided parameters
        :param builder: builder object which contains all necessary parameters on which db methods will be executed
        """

        # Initializing the parent class constructor
        super(CouchbaseOperation, self).__init__(builder)

    def restart_couchbase(self):
        """stop the couchbase service and then start again"""
        self.stop_couchbase()
        self.start_couchbase()

    def start_couchbase(self):
        """ start the couchbase service"""
        logger.debug("Starting couchbase services")
        # check if we need sudo
        need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)
        command = CommandFactory.start_couchbase(self.repository.cb_install_path, need_sudo, self.repository.uid)
        logger.debug(command)
        utilities.execute_bash(self.connection, command)
        server_status = Status.INACTIVE

        helper_lib.sleepForSecond(10)

        #Waiting for one minute to start the server
        end_time = time.time() + 60

        #break the loop either end_time is exceeding from 1 minute or server is successfully started
        while time.time() < end_time and server_status == Status.INACTIVE:
            helper_lib.sleepForSecond(1) # waiting for 1 second
            server_status = self.status() # fetching status

        # if the server is not running even in 60 seconds, then stop the further execution
        if server_status == Status.INACTIVE:
            raise CouchbaseServicesError("Have failed to start couchbase server")


    def stop_couchbase(self):
        """ stop the couchbase service"""
        try:
            logger.debug("Stopping couchbase services")
            need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)
            command = CommandFactory.stop_couchbase(self.repository.cb_install_path, need_sudo, self.repository.uid)
            utilities.execute_bash(self.connection, command)
            end_time = time.time() + 60
            server_status = Status.ACTIVE
            while time.time() < end_time and server_status == Status.ACTIVE:
                helper_lib.sleepForSecond(1)  # waiting for 1 second
                server_status = self.status()  # fetching status
            if server_status == Status.ACTIVE:
                raise CouchbaseServicesError("Have failed to stop couchbase server")
        except CouchbaseServicesError as err:
            raise err
        except Exception as err:
            if self.status() == Status.INACTIVE:
                logger.debug("Seems like couchbase service is not running. {}".format(err.message))
            else:
                raise CouchbaseServicesError(err.message)


    def status(self):
        """Check the server status. Healthy or Warmup could be one status if the server is running"""
        try:
            command = CommandFactory.server_info(self.repository.cb_shell_path, self.connection.environment.host.name,
                                                 self.parameters.couchbase_port, self.parameters.couchbase_admin)

            kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
            server_info, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)

            status = helper_lib.get_value_of_key_from_json(server_info, 'status')
            if status.strip() == StatusIsActive:
                logger.debug("Server status is:  {}".format("ACTIVE"))
                return Status.ACTIVE
            else:
                logger.debug("Server status is:  {}".format("INACTIVE"))
                return Status.INACTIVE
        except Exception as error:
            if re.search("Unable to connect to host at", error.message):
                logger.debug("Couchbase service is not running")
            return Status.INACTIVE

    def make_directory(self, directory_path, force_env_user=False):
        """
        Create a directory and set the permission level 775
        :param directory_path: The directory path
        :return: None
        """
        logger.debug("Creating Directory {} ".format(directory_path))
        env = {'directory_path': directory_path}
        if force_env_user:
            need_sudo = False
        else:
            need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)
        command = CommandFactory.make_directory(directory_path, need_sudo, self.repository.uid)
        utilities.execute_bash(self.connection, command)
        logger.debug("Changing permission of directory path {}".format(directory_path))
        command = CommandFactory.change_permission(directory_path, need_sudo, self.repository.uid)
        utilities.execute_bash(self.connection, command)
        logger.debug("Changed the permission of directory")

    def create_config_dir(self):
        """create and return the hidden folder directory with name 'delphix'"""
        logger.debug("Finding toolkit Path...")
        command = CommandFactory.get_dlpx_bin()
        bin_directory, std_err, exit_code = utilities.execute_bash(self.connection, command)
        if bin_directory is None or bin_directory == "":
            raise Exception("Failed to find the toolkit directory")
        # Toolkit directory tested on linux x86_64Bit is 6 level below jq path
        loop_var = 6
        while loop_var:
            bin_directory = os.path.dirname(bin_directory)
            loop_var = loop_var - 1
        dir_name = bin_directory + "/" + DELPHIX_HIDDEN_FOLDER
        if not helper_lib.check_dir_present(self.connection, dir_name):
            self.make_directory(dir_name, force_env_user=True)
        return dir_name
            

    def source_bucket_list(self):
        """
        return all buckets exist on source server. Also contains the information bucketType, ramQuota, ramUsed,
        numReplicas
        :return:
        """
        # See the bucket list on source server
        logger.debug("Collecting bucket list information present on source server ")
        env = {ENV_VAR_KEY: {'password': self.staged_source.parameters.xdcr_admin_password}}
        command = CommandFactory.get_source_bucket_list(self.repository.cb_shell_path,
                                                        self.source_config.couchbase_src_host,
                                                        self.source_config.couchbase_src_port,
                                                        self.staged_source.parameters.xdcr_admin)
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name=command, **env)
        if bucket_list == "[]" or bucket_list is None:
            return []
        else:
            logger.debug("clean up json")
            bucket_list = bucket_list.replace("u'","'")
            bucket_list = bucket_list.replace("'", "\"")
            bucket_list = bucket_list.replace("True", "\"True\"")
            bucket_list = bucket_list.replace("False", "\"False\"")
            logger.debug("parse json")
            bucket_list_dict = json.loads(bucket_list)
            bucket_list_dict = map(helper_lib.remap_bucket_json, bucket_list_dict)

        logger.debug("Source Bucket Information {}".format(bucket_list_dict))
        return bucket_list_dict

    def source_bucket_list_offline(self, filename):
        """
        This function will be used in CB backup manager. It will return the same output as by
        source_bucket_list method. To avoid source/production server dependency this function will be used.
        In a file, put all the bucket related information of source server. This function will cat and return the
        contents of that file. It is useful for cb backup manager ingestion mechanism
        FilePath : <Toolkit-Directory-Path>/couchbase_src_bucket_info
        In this file add output of below command:
        /opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091  --username $username --password $pass
        From here all source bucket list information we can fetch and other related data of this bucket should be placed
        at backup location.
        :param filename: filename(couchbase_src_bucket_info.cfg) where bucket information is kept.
        :return: bucket list information
        """

        def get_date(x):
            w = x.replace('/opt/couchbase/backup/PROD','')
            g = re.match(r'/(.+?)/.*',w)
            if g:
                return g.group(1)
            else:
                return ''

        logger.debug(
            "Reading bucket list information of source server from {} ".format(filename))

        logger.debug(self.parameters.couchbase_bak_loc)
        logger.debug(self.parameters.couchbase_bak_repo)

        need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)

        command = CommandFactory.get_backup_bucket_list(os.path.join(self.parameters.couchbase_bak_loc, self.parameters.couchbase_bak_repo), need_sudo, self.repository.uid)
        logger.debug("Bucket search command: {}".format(command))
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name=command, callback_func=self.ignore_err)

        backup_list = bucket_list.split('\n')
        logger.debug("Bucket search output: {}".format(backup_list))
        date_list = map(get_date, backup_list) 
        date_list.sort()
        logger.debug("date list: {}".format(date_list))
        files_to_process = [ x for x in backup_list if date_list[-1] in x ]

        logger.debug(files_to_process)

        bucket_list_dict = []

        for f in files_to_process:
            command = CommandFactory.cat(f, need_sudo, self.repository.uid)
            logger.debug("cat command: {}".format(command))
            bucket_file_content, error, exit_code = utilities.execute_bash(self.connection, command_name=command)
            logger.debug(bucket_file_content)
            bucket_json = json.loads(bucket_file_content)
            bucket_list_dict.append(remap_bucket_json(bucket_json))


        # command = CommandFactory.read_file(filename)
        # bucket_list, error, exit_code = utilities.execute_bash(self.connection, command)
        # if bucket_list == "" or bucket_list is None:
        #     return []
        # bucket_list = bucket_list.split("\n")
        logger.debug("Bucket search output: {}".format(bucket_list_dict))
        return bucket_list_dict

    def node_init(self):
        """
        This method initializes couchbase server node. Where user sets different required paths
        :return: None
        """
        logger.debug("Initializing the NODE")
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        command = CommandFactory.node_init(self.repository.cb_shell_path, self.parameters.couchbase_port,
                                           self.parameters.couchbase_admin, self.parameters.mount_path)
        logger.debug("Node init: {}".format(command))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
        logger.debug("Command Output {} ".format(command_output))

    def get_config_directory(self):
        """
        Hidden directory path inside mount directory will be returned. which is created in method create_config_dir
        :return: Return the config directory
        """

        config_path = self.parameters.mount_path + "/" + DELPHIX_HIDDEN_FOLDER
        logger.debug("Config folder is: {}".format(config_path))
        return config_path

    def get_config_file_path(self):
        """
        :return: Config file created inside the hidden folder.
        """
        config_file_path = self.get_config_directory() + "/" + CONFIG_FILE_NAME
        logger.debug("Config filepath is: {}".format(config_file_path))
        return config_file_path


    # Defined for future updates
    def get_indexes_definition(self):
        # by default take from staging but later take from source
        logger.debug("Finding indexes....")
        env = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}

        if self.dSource:
            hostname = self.parameters.couchbase_host
        else:
            hostname = self.connection.environment.host.name

        cmd = CommandFactory.get_indexes_name(hostname, self.parameters.couchbase_port, self.parameters.couchbase_admin)
        logger.debug("env detail is : ".format(env))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)
        logger.debug("Indexes are {}".format(command_output))
        indexes_raw = json.loads(command_output)
        indexes = []
        for i in indexes_raw['indexes']:
            indexes.append(i['definition'].replace('defer_build":true','defer_build":false'))
        return indexes

    # Defined for future updates
    def build_index(self, index_def):
        env = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        cmd = CommandFactory.build_index(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),self.connection.environment.host.name, self.parameters.couchbase_port, self.parameters.couchbase_admin, index_def)
        logger.debug("building index cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)
        logger.debug("command_output is ".format(command_output))
        return command_output


    def save_config(self):

        # TODO
        # Error handling

        targetdir = self.get_config_directory()
        filename = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)

        cmd = CommandFactory.os_cp(filename, targetdir, need_sudo, self.repository.uid)
        logger.debug("save config cp: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        filename = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        cmd = CommandFactory.os_cp(filename, targetdir, need_sudo, self.repository.uid)
        logger.debug("save init cp: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 


    def restore_config(self):

        # TODO
        # Error handling

        sourcefile = os.path.join(self.get_config_directory(),"config.dat")
        targetfile = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)

        cmd = CommandFactory.os_cp(sourcefile, targetfile, need_sudo, self.repository.uid)
        logger.debug("restore config cp: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        sourcefile = os.path.join(self.get_config_directory(),"local.ini")
        targetfile = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        cmd = CommandFactory.os_cp(sourcefile, targetfile, need_sudo, self.repository.uid)
        logger.debug("restore init cp: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 


    def delete_config(self):

        # TODO:
        # error handling

        filename = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        
        cmd = CommandFactory.check_file(filename)
        logger.debug("check file cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, callback_func=self.ignore_err) 

        if exit_code == 0 and "Found" in command_output: 
            cmd = CommandFactory.os_mv(filename, "{}.bak".format(filename))
            logger.debug("rename config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        filename = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        cmd = CommandFactory.sed(filename, 's/view_index_dir.*//')
        logger.debug("sed config cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        cmd = CommandFactory.sed(filename, 's/database_dir.*//')
        logger.debug("sed config cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        cmd = CommandFactory.change_permission(filename)
        logger.debug("chmod config cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 
        

    def ignore_err(self, input):
        return True


if __name__ == "__main__":
    print "Checking Couchbase Class"
    test_object = CouchbaseOperation(Resource.ObjectBuilder.set_dsource(True).build())
    print (test_object.get_config_file_path.__doc__)
