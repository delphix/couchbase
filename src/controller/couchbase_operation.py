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
        command = CommandFactory.start_couchbase(self.repository.cb_install_path)
        utilities.execute_bash(self.connection, command)
        server_status = Status.INACTIVE

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
            command = CommandFactory.stop_couchbase(self.repository.cb_install_path)
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

    def make_directory(self, directory_path):
        """
        Create a directory and set the permission level 775
        :param directory_path: The directory path
        :return: None
        """
        logger.debug("Creating Directory {} ".format(directory_path))
        env = {'directory_path': directory_path}
        command = CommandFactory.make_directory(directory_path)
        utilities.execute_bash(self.connection, command)
        logger.debug("Changing permission of directory path {}".format(directory_path))
        command = CommandFactory.change_permission(directory_path)
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
            self.make_directory(dir_name)
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
        if bucket_list == "" or bucket_list is None:
            return []
        bucket_list = bucket_list.split("\n")
        logger.debug("Source Bucket Information {}".format(bucket_list))
        return bucket_list

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
        logger.debug(
            "Reading bucket list information of source server from {} ".format(filename))
        command = CommandFactory.read_file(filename)
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command)
        if bucket_list == "" or bucket_list is None:
            return []
        bucket_list = bucket_list.split("\n")
        return bucket_list

    def node_init(self):
        """
        This method initializes couchbase server node. Where user sets different required paths
        :return: None
        """
        logger.debug("Initializing the NODE")
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        command = CommandFactory.node_init(self.repository.cb_shell_path, self.parameters.couchbase_port,
                                           self.parameters.couchbase_admin, self.parameters.mount_path)
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


if __name__ == "__main__":
    print "Checking Couchbase Class"
    test_object = CouchbaseOperation(Resource.ObjectBuilder.set_dsource(True).build())
    print (test_object.get_config_file_path.__doc__)
