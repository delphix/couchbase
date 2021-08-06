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
import inspect

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
from db_commands import constants

from dlpx.virtualization.platform.exceptions import UserError

logger = logging.getLogger(__name__)


class CouchbaseOperation(_BucketMixin, _ClusterMixin, _ReplicationMixin, _XDCrMixin, _CBBackupMixin):

    def __init__(self, builder, node_connection=None):
        """
        Main class through which other modules can run databases operations on provided parameters
        :param builder: builder object which contains all necessary parameters on which db methods will be executed
        :param node_connection: connection to node, if this is not a default one
        """

        logger.debug("Object initialization")
        # Initializing the parent class constructor
        super(CouchbaseOperation, self).__init__(builder)

        if node_connection is not None:
            self.connection = node_connection

        self.__need_sudo = helper_lib.need_sudo(self.connection, self.repository.uid, self.repository.gid)
        self.__uid = self.repository.uid
        self.__gid = self.repository.gid


    @property
    def need_sudo(self):
        return self.__need_sudo

    @property
    def uid(self):
        return self.__uid

    @property
    def gid(self):
        return self.__gid


    def run_couchbase_command(self, couchbase_command, **kwargs):
        logger.debug('run_couchbase_command')
        logger.debug('couchbase_command: {}'.format(couchbase_command))
        if "password" in kwargs:
            password = kwargs.pop('password')
        else:
            password = self.parameters.couchbase_admin_password

        if "username" in kwargs:
            username = kwargs.pop('username')
        else:
            username = self.parameters.couchbase_admin

        if "hostname" in kwargs:
            hostname = kwargs.pop('hostname')
        else:
            hostname = self.connection.environment.host.name

        env = {"password": password}

        if "newpass" in kwargs:
            # for setting a new password
            env["newpass"] = kwargs.pop('newpass')


        autoparams = [ "shell_path", "install_path", "username", "port", "sudo", "uid", "hostname"]

        new_kwargs = {k: v for k, v in kwargs.items() if k not in autoparams}

        method_to_call = getattr(CommandFactory, couchbase_command)
        command = method_to_call(shell_path=self.repository.cb_shell_path,
                                 install_path=self.repository.cb_install_path,
                                 username=username,
                                 port=self.parameters.couchbase_port,
                                 sudo=self.need_sudo,
                                 uid=self.uid,
                                 hostname=hostname,
                                 **new_kwargs)

        logger.debug("couchbase command to run: {}".format(command))
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, command, environment_vars=env)
        return [stdout, stderr, exit_code]


    def run_os_command(self, os_command, **kwargs):

        

        method_to_call = getattr(CommandFactory, os_command)
        command = method_to_call(sudo=self.need_sudo, 
                                 uid=self.uid,
                                 **kwargs)

        logger.debug("os command to run: {}".format(command))
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, command)
        return [stdout, stderr, exit_code]


    def restart_couchbase(self, provision=False):
        """stop the couchbase service and then start again"""
        self.stop_couchbase()
        self.start_couchbase(provision)

    def start_couchbase(self, provision=False, no_wait=False):
        """ start the couchbase service"""
        logger.debug("Starting couchbase services")

        self.run_couchbase_command('start_couchbase')
        server_status = Status.INACTIVE

        helper_lib.sleepForSecond(10)

        if no_wait:
            logger.debug("no wait - leaving start procedure")
            return

        #Waiting for one minute to start the server
        # for prox to investigate
        end_time = time.time() + 3660

        #break the loop either end_time is exceeding from 1 minute or server is successfully started
        while time.time() < end_time and server_status == Status.INACTIVE:
            helper_lib.sleepForSecond(1) # waiting for 1 second
            server_status = self.status(provision) # fetching status
            logger.debug("server status {}".format(server_status))

        # if the server is not running even in 60 seconds, then stop the further execution
        if server_status == Status.INACTIVE:
            raise CouchbaseServicesError("Have failed to start couchbase server")


    def stop_couchbase(self):
        """ stop the couchbase service"""
        try:
            logger.debug("Stopping couchbase services")
            self.run_couchbase_command('stop_couchbase')

            end_time = time.time() + 60
            server_status = Status.ACTIVE
            while time.time() < end_time and server_status == Status.ACTIVE:
                helper_lib.sleepForSecond(1)  # waiting for 1 second
                server_status = self.status()  # fetching status


            logger.debug("Leaving stop loop")    
            if server_status == Status.ACTIVE:
                logger.debug("Have failed to stop couchbase server")  
                raise CouchbaseServicesError("Have failed to stop couchbase server")
        except CouchbaseServicesError as err:
            logger.debug("Error: {}".format(err))  
            raise err
        except Exception as err:
            logger.debug("Exception Error: {}".format(err)) 
            if self.status() == Status.INACTIVE:
                logger.debug("Seems like couchbase service is not running. {}".format(err.message))
            else:
                raise CouchbaseServicesError(err.message)


    def ip_file_name(self):
        
        ip_file = "{}/../var/lib/couchbase/ip".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        # check_file_command = CommandFactory.check_file(ip_file, sudo=self.need_sudo, uid=self.uid)
        # check_ip_file, check_ip_file_err, exit_code = utilities.execute_bash(self.connection, check_file_command, callback_func=self.ignore_err)


        check_ip_file, check_ip_file_err, exit_code = self.run_os_command(
                                                        os_command='check_file',
                                                        file_path=ip_file
                                                      )

        if not (exit_code == 0 and "Found" in check_ip_file): 
            ip_file = "{}/../var/lib/couchbase/ip_start".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))


        logger.debug("IP file is {}".format(ip_file))
        return ip_file


    def staging_bootstrap_status(self):
        logger.debug("staging_bootstrap_status")

        try:


            server_info_out, std_err, exit_code = self.run_couchbase_command(
                                                    couchbase_command='couchbase_server_info',
                                                    hostname='127.0.0.1'
                                                )


            # kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
            # username = self.parameters.couchbase_admin


            # command = CommandFactory.server_info(self.repository.cb_shell_path, '127.0.0.1',
            #                                      self.parameters.couchbase_port, username)
            # logger.debug("Status command {}".format(command))
            # server_info, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)

            #logger.debug("Status output: {}".format(server_info))
            
            status = helper_lib.get_value_of_key_from_json(server_info_out, 'status')
            if status.strip() == StatusIsActive:
                logger.debug("Server status is:  {}".format("ACTIVE"))
                return Status.ACTIVE
            else:
                logger.debug("Server status is:  {}".format("INACTIVE"))
                return Status.INACTIVE
            
            

        except Exception as error:
            # TODO
            # rewrite it 
            logger.debug("Exception: {}".format(str(error)))
            if re.search("Unable to connect to host at", error.message):
                logger.debug("Couchbase service is not running")
            return Status.INACTIVE

    def status(self, provision=False):
        """Check the server status. Healthy or Warmup could be one status if the server is running"""
        
        logger.debug("checking status")
        logger.debug(self.connection)
        try:

            if provision==True:
                username = self.snapshot.couchbase_admin
                password = self.snapshot.couchbase_admin_password

            else:
                password = self.parameters.couchbase_admin_password
                username = self.parameters.couchbase_admin


            #TODO
            # Check if there is a mount point - even a started Couchbase without mountpoint means VDB
            # is down or corrupted 
            # Couchbase with config file can start and recreate empty buckets if there is no mount point
            # for future version - maybe whole /opt/couchbase/var directory should be virtualized like for Docker
            # to avoid problems 

            logger.debug("Checking for mount points")
            mount_point_state = helper_lib.check_server_is_used(self.connection, self.parameters.mount_path)
            logger.debug("Status of mount point {}".format(mount_point_state))

            if mount_point_state == Status.INACTIVE:
                logger.error("There is no mount point VDB is down regardless Couchbase status")
                return Status.INACTIVE

            
            ip_file = self.ip_file_name()

            # read_file_command = CommandFactory.cat(ip_file, sudo=self.need_sudo, uid=self.uid)
            # logger.debug("read file command {}".format(read_file_command))

            # read_ip_file, std_err, exit_code = utilities.execute_bash(self.connection, read_file_command)
            # logger.debug("read file {}".format(read_ip_file))


            read_ip_file, std_err, exit_code = self.run_os_command(
                                                    os_command='cat',
                                                    path=ip_file
                                                )

            server_info, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='get_server_list',
                                                hostname='127.0.0.1',
                                                username=username,
                                                password=password)

            #status = helper_lib.get_value_of_key_from_json(server_info, 'status')
            
            for line in server_info.split("\n"):
                logger.debug("Checking line: {}".format(line))
                if read_ip_file in line:
                    logger.debug("Checking IP: {}".format(read_ip_file))
                    if "unhealthy" in line:
                        logger.error("We have unhealthy active node")
                        return Status.INACTIVE
                    if "healthy" in line:
                        logger.debug("We have healthy active node")
                        return Status.ACTIVE
            
            
            return Status.INACTIVE

        except Exception as error:
            # TODO
            # rewrite it 
            logger.debug("Exception: {}".format(str(error)))
            if re.search("Unable to connect to host at", error.message):
                logger.debug("Couchbase service is not running")
            return Status.INACTIVE

    def make_directory(self, directory_path, force_env_user=False):
        """
        Create a directory and set the permission level 775
        :param directory_path: The directory path
        :return: None
        """

        #TODO
        # add error handling for OS errors

        logger.debug("Creating Directory {} ".format(directory_path))
        if force_env_user:
            need_sudo = False
        else:
            need_sudo = self.need_sudo


        command_output, std_err, exit_code = self.run_os_command(
                                        os_command='make_directory',
                                        directory_path=directory_path
                                    )
            
        # command = CommandFactory.make_directory(directory_path, need_sudo, self.uid)
        # utilities.execute_bash(self.connection, command)

        logger.debug("Changing permission of directory path {}".format(directory_path))

        # command = CommandFactory.change_permission(directory_path, need_sudo, self.uid)
        # utilities.execute_bash(self.connection, command)

        command_output, std_err, exit_code = self.run_os_command(
                                        os_command='change_permission',
                                        path=directory_path
                                    )

        logger.debug("Changed the permission of directory")

    def create_config_dir(self):
        """create and return the hidden folder directory with name 'delphix'"""

        #TODO
        # clean up error handling

        logger.debug("Finding toolkit Path...")
        bin_directory, std_err, exit_code = self.run_os_command(
                                                os_command='get_dlpx_bin'
                                            )


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

        # env = {ENV_VAR_KEY: {'password': self.staged_source.parameters.xdcr_admin_password}}
        # command = CommandFactory.get_source_bucket_list(self.repository.cb_shell_path,
        #                                                 self.source_config.couchbase_src_host,
        #                                                 self.source_config.couchbase_src_port,
        #                                                 self.staged_source.parameters.xdcr_admin)
        # bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name=command, **env)

        bucket_list, error, exit_code = self.run_couchbase_command(
                                                couchbase_command='get_source_bucket_list',
                                                source_hostname=self.source_config.couchbase_src_host,
                                                source_port=self.source_config.couchbase_src_port,
                                                source_username=self.staged_source.parameters.xdcr_admin,
                                                password=self.staged_source.parameters.xdcr_admin_password
                                            )


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


    def get_backup_date(self, x):
        w = x.replace('{}/{}'.format(self.parameters.couchbase_bak_loc, self.parameters.couchbase_bak_repo),'')
        g = re.match(r'/(.+?)/.*',w)
        if g:
            return g.group(1)
        else:
            return ''

    def source_bucket_list_offline(self):
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



        logger.debug(self.parameters.couchbase_bak_loc)
        logger.debug(self.parameters.couchbase_bak_repo)

        
        # command = CommandFactory.get_backup_bucket_list(os.path.join(self.parameters.couchbase_bak_loc, self.parameters.couchbase_bak_repo), self.need_sudo, self.uid)
        # logger.debug("Bucket search command: {}".format(command))
        # bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name=command, callback_func=self.ignore_err)


        bucket_list, error, exit_code = self.run_os_command(
                                                os_command='get_backup_bucket_list',
                                                path=os.path.join(self.parameters.couchbase_bak_loc, self.parameters.couchbase_bak_repo)
                                            )


        backup_list = bucket_list.split('\n')
        logger.debug("Bucket search output: {}".format(backup_list))
        date_list = map(self.get_backup_date, backup_list) 
        date_list.sort()
        logger.debug("date list: {}".format(date_list))
        files_to_process = [ x for x in backup_list if date_list[-1] in x ]

        logger.debug(files_to_process)

        bucket_list_dict = []

        for f in files_to_process:
            # command = CommandFactory.cat(f, self.need_sudo, self.uid)
            # logger.debug("cat command: {}".format(command))
            # bucket_file_content, error, exit_code = utilities.execute_bash(self.connection, command_name=command)

            bucket_file_content, error, exit_code = self.run_os_command(
                                        os_command='cat',
                                        path=f
                                    )


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

    def node_init(self, nodeno=1):
        """
        This method initializes couchbase server node. Where user sets different required paths
        :return: None
        """
        logger.debug("Initializing the NODE")

        command_output, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='node_init',
                                                data_path="{}/data_{}".format(self.parameters.mount_path, nodeno)
                                            )

        # kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # command = CommandFactory.node_init(self.repository.cb_shell_path, self.parameters.couchbase_port,
        #                                    self.parameters.couchbase_admin, )
        # logger.debug("Node init: {}".format(command))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)

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
        password = self.parameters.couchbase_admin_password
        user = self.parameters.couchbase_admin
        port = self.parameters.couchbase_port
        if self.dSource:
            if self.parameters.d_source_type == constants.CBBKPMGR:
                hostname = self.parameters.couchbase_host
            else:
                port = self.source_config.couchbase_src_port
                user = self.staged_source.parameters.xdcr_admin
                password = self.staged_source.parameters.xdcr_admin_password
                hostname = self.source_config.couchbase_src_host
        else:
            hostname = self.connection.environment.host.name

        # cmd = CommandFactory.get_indexes_name(hostname, port, user)
        # logger.debug("command for indexes is : {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)

        command_output, std_err, exit_code = self.run_couchbase_command(
                                    couchbase_command='get_indexes_name',
                                    hostname=hostname,
                                    username=user,
                                    port=port,
                                    password=password
                                )


        logger.debug("Indexes are {}".format(command_output))
        indexes_raw = json.loads(command_output)
        indexes = []

        logger.debug("dSource type for indexes: {}".format(self.parameters.d_source_type))

        if self.parameters.d_source_type == constants.CBBKPMGR:
            logger.debug("Only build for backup ingestion")

            buckets = {}
            for i in indexes_raw['indexes']:
                if i['bucket'] in buckets:
                    buckets[i['bucket']].append(i['indexName'])
                else:
                    buckets[i['bucket']] = [ i['indexName'] ]

            for buc, ind in buckets.items():
                ind_def = 'build index on `{}` (`{}`)'.format(buc, '`,`'.join(ind))
                indexes.append(ind_def)

        else:
            # full definition for replication

            for i in indexes_raw['indexes']:
                indexes.append(i['definition'].replace('defer_build":true','defer_build":false'))
        return indexes

    # Defined for future updates
    def build_index(self, index_def):
        command_output, std_err, exit_code = self.run_couchbase_command(
                                    couchbase_command='build_index',
                                    base_path=helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),
                                    index_def=index_def
                                )


        # env = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # cmd = CommandFactory.build_index(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),self.connection.environment.host.name, self.parameters.couchbase_port, self.parameters.couchbase_admin, index_def)
        # logger.debug("building index cmd: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)

        logger.debug("command_output is {}".format(command_output))
        return command_output


    def check_index_build(self):
        # env = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # cmd = CommandFactory.check_index_build(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),self.connection.environment.host.name, self.parameters.couchbase_port, self.parameters.couchbase_admin)
        # logger.debug("check_index_build cmd: {}".format(cmd))

        end_time = time.time() + 3660

        tobuild = 1

        #break the loop either end_time is exceeding from 1 minute or server is successfully started
        while time.time() < end_time and tobuild <> 0:

            command_output, std_err, exit_code = self.run_couchbase_command(
                                        couchbase_command='check_index_build',
                                        base_path=helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path)
                                    )


            #command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)
            logger.debug("command_output is {}".format(command_output))
            logger.debug("std_err is {}".format(std_err))
            logger.debug("exit_code is {}".format(exit_code))
            try:
                command_output_dict = json.loads(command_output)
                logger.debug("dict {}".format(command_output_dict))
                tobuild = command_output_dict['results'][0]['unbuilt']
                logger.debug("to_build is {}".format(tobuild))
                helper_lib.sleepForSecond(30) # waiting for 1 second
            except Exception as e:
                logger.debug(str(e))




    def save_config(self, what, nodeno=1):

        # TODO
        # Error handling

        targetdir = self.get_config_directory()
        # if what == 'parent':
        #     target_config_filename = os.path.join(targetdir,"config_parent.dat")
        #     target_local_filename = os.path.join(targetdir,"local_parent.ini")
        #     target_encryption_filename = os.path.join(targetdir,"encrypted_data_keys_parent")
        # else:
        #     target_config_filename = os.path.join(targetdir,"config_current.dat")
        #     target_local_filename = os.path.join(targetdir,"local_current.ini")
        #     target_encryption_filename = os.path.join(targetdir,"encrypted_data_keys_current")


        target_config_filename = os.path.join(targetdir,"config.dat_{}".format(nodeno))
        target_local_filename = os.path.join(targetdir,"local.ini_{}".format(nodeno))
        target_encryption_filename = os.path.join(targetdir,"encrypted_data_keys_{}".format(nodeno))

        # replace it by node number - to validate in the future
        # ip_file = self.ip_file_name()
        # if "start" in ip_file:
        #     target_ip_filename = os.path.join(targetdir,"ip_start_{}".format(nodeno))
        # else:
        #     target_ip_filename = os.path.join(targetdir,"ip_{}".format(nodeno))

        if nodeno == 1:
            ip_file = "{}/../var/lib/couchbase/ip".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
            target_ip_filename = os.path.join(targetdir,"ip_{}".format(nodeno))
        else:
            ip_file = "{}/../var/lib/couchbase/ip_start".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
            target_ip_filename = os.path.join(targetdir,"ip_start_{}".format(nodeno))


        filename = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        # cmd = CommandFactory.os_cp(filename, target_config_filename, self.need_sudo, self.uid)
        # logger.debug("save config cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=filename,
                                                        trgname=target_config_filename
                                                      )

        logger.debug("save config.dat cp exit code: {}".format(exit_code))

        if exit_code != 0:
            raise UserError("Error saving configuration file: config.dat", "Check sudo or user privileges to read Couchbase config.dat file", std_err)


        # encryption data keys may not exist on Community edition

        filename = "{}/../var/lib/couchbase/config/encrypted_data_keys".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        check_encrypted_data_keys, check_ip_file_err, exit_code = self.run_os_command(
                                                        os_command='check_file',
                                                        file_path=filename
                                                      )

        if exit_code == 0 and "Found" in check_encrypted_data_keys: 
            # cmd = CommandFactory.os_cp(filename, target_encryption_filename, self.need_sudo, self.uid)
            # logger.debug("save encrypted_data_keys cp: {}".format(cmd))
            # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 
            command_output, std_err, exit_code = self.run_os_command(
                                                            os_command='os_cp',
                                                            srcname=filename,
                                                            trgname=target_encryption_filename
                                                        )

            logger.debug("save encrypted_data_keys cp exit code: {}".format(exit_code))
            if exit_code != 0:
                raise UserError("Error saving configuration file: encrypted_data_keys", "Check sudo or user privileges to read Couchbase encrypted_data_keys file", std_err)


        
        # cmd = CommandFactory.os_cp(ip_file, target_ip_filename, self.need_sudo, self.uid)
        # logger.debug("save ip cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=ip_file,
                                                        trgname=target_ip_filename
                                                    )      

        logger.debug("save {} cp exit code: {}".format(ip_file, exit_code))

        if exit_code != 0:
            raise UserError("Error saving configuration file: {}".format(ip_file), "Check sudo or user privileges to read Couchbase {} file".format(ip_file), std_err)
  

        filename = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        # cmd = CommandFactory.os_cp(filename, target_local_filename, self.need_sudo, self.uid)
        # logger.debug("save init cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=filename,
                                                        trgname=target_local_filename
                                                    )   

        logger.debug("save local.ini cp exit code: {}".format(exit_code))
        if exit_code != 0:
            raise UserError("Error saving configuration file: local.ini", "Check sudo or user privileges to read Couchbase local.ini file", std_err)



    def check_cluster_notconfigured(self):

        logger.debug("check_cluster")

        command_output, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='get_server_list',
                                                hostname=self.connection.environment.host.name)

        if "unknown pool" in command_output:
            return True
        else:
            return False


    def check_cluster_configured(self):

        logger.debug("check_cluster configured")

        command_output, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='get_server_list',
                                                hostname=self.connection.environment.host.name)

        if "healthy active" in command_output:
            return True
        else:
            return False



    def check_config(self):

        filename = os.path.join(self.get_config_directory(),"config.dat")
        cmd = CommandFactory.check_file(filename)
        logger.debug("check file cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, callback_func=self.ignore_err) 

        if exit_code == 0 and "Found" in command_output: 
            return True
        else:
            return False  

    def restore_config(self, what, nodeno=1):

        # TODO
        # Error handling

        sourcedir = self.get_config_directory()
        # if what == 'parent':
        #     source_config_file = os.path.join(sourcedir,"config_parent.dat")
        #     source_local_filename = os.path.join(sourcedir,"local_parent.ini")
        #     source_encryption_keys = os.path.join(sourcedir,"encrypted_data_keys_parent")
        # else:
        #     source_config_file = os.path.join(sourcedir,"config_current.dat")
        #     source_local_filename = os.path.join(sourcedir,"local_current.ini")
        #     source_encryption_keys = os.path.join(sourcedir,"encrypted_data_keys_current")



        source_config_file = os.path.join(sourcedir,"config.dat_{}".format(nodeno))
        source_local_filename = os.path.join(sourcedir,"local.ini_{}".format(nodeno))
        source_encryption_keys = os.path.join(sourcedir,"encrypted_data_keys_{}".format(nodeno))

        
        source_ip_file = os.path.join(sourcedir,"ip_{}".format(nodeno))
        target_ip_file = "{}/../var/lib/couchbase/ip".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        delete_ip_file = "{}/../var/lib/couchbase/ip_start".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        # check_file_command = CommandFactory.check_file(source_ip_file, sudo=self.need_sudo, uid=self.uid)
        # check_ip_file, check_ip_file_err, exit_code = utilities.execute_bash(self.connection, check_file_command, callback_func=self.ignore_err)

        check_ip_file, check_ip_file_err, exit_code = self.run_os_command(
                                                        os_command='check_file',
                                                        file_path=source_ip_file
                                                      )


        if not (exit_code == 0 and "Found" in check_ip_file): 
            source_ip_file = os.path.join(sourcedir,"ip_start_{}".format(nodeno))
            target_ip_file = "{}/../var/lib/couchbase/ip_start".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
            delete_ip_file = "{}/../var/lib/couchbase/ip".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        logger.debug("IP file is {}".format(source_ip_file))

        ip_filename = os.path.join(sourcedir,"ip_{}".format(source_ip_file))

        targetfile = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        # cmd = CommandFactory.os_cp(source_config_file, targetfile, self.need_sudo, self.uid)
        # logger.debug("restore config cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=source_config_file,
                                                        trgname=targetfile
                                                    )   



        check_encrypted_data_keys, check_ip_file_err, exit_code = self.run_os_command(
                                                        os_command='check_file',
                                                        file_path=source_encryption_keys
                                                      )

        logger.debug("Check check_encrypted_data_keys - exit_code: {} stdout: {}".format(exit_code, check_encrypted_data_keys))

        if  exit_code == 0 and "Found" in check_encrypted_data_keys: 
            targetfile = "{}/../var/lib/couchbase/config/encrypted_data_keys".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
            # cmd = CommandFactory.os_cp(source_encryption_keys, targetfile, self.need_sudo, self.uid)
            # logger.debug("restore encrypted_data_keys cp: {}".format(cmd))
            # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

            command_output, std_err, exit_code = self.run_os_command(
                                                            os_command='os_cp',
                                                            srcname=source_encryption_keys,
                                                            trgname=targetfile
                                                        )  

        
        # cmd = CommandFactory.os_cp(source_ip_file, target_ip_file, self.need_sudo, self.uid)
        # logger.debug("restore ip cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 




        check_ip_delete_file, check_ip_delete_file, check_ip_exit_code = self.run_os_command(
                                                        os_command='check_file',
                                                        file_path=delete_ip_file
                                                      )

        logger.debug("Check delete old ip_file - exit_code: {} stdout: {}".format(check_ip_exit_code, check_ip_delete_file))

#        if  check_ip_exit_code == 0 and "Found" in check_ip_delete_file: 
        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_mv',
                                                        srcname=delete_ip_file,
                                                        trgname="{}.bak".format(delete_ip_file)
                                                    )  

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=source_ip_file,
                                                        trgname=target_ip_file
                                                    )  


        targetfile = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        # cmd = CommandFactory.os_cp(source_local_filename, targetfile, self.need_sudo, self.uid)
        # logger.debug("restore init cp: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='os_cp',
                                                        srcname=source_local_filename,
                                                        trgname=targetfile
                                                    )  

        if what == 'parent':
            #local.ini needs to have a proper entry 
            filename = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
            newpath = "{}/data_{}".format(self.parameters.mount_path, nodeno)
            cmd = CommandFactory.sed(filename, 's|view_index_dir.*|view_index_dir={}|'.format(newpath), self.need_sudo, self.uid)
            logger.debug("sed config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

            cmd = CommandFactory.sed(filename, 's|database_dir.*|database_dir={}|'.format(newpath), self.need_sudo, self.uid)
            logger.debug("sed config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 
        


    def delete_config(self):

        # TODO:
        # error handling

        filename = "{}/../var/lib/couchbase/config/config.dat".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))

        
        
        cmd = CommandFactory.check_file(filename, self.need_sudo, self.uid)
        logger.debug("check file cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, callback_func=self.ignore_err) 




        if exit_code == 0 and "Found" in command_output: 
            cmd = CommandFactory.os_mv(filename, "{}.bak".format(filename), self.need_sudo, self.uid)
            logger.debug("rename config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        filename = "{}/../etc/couchdb/local.ini".format(helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path))
        # cmd = CommandFactory.sed(filename, 's/view_index_dir.*//', self.need_sudo, self.uid)
        # logger.debug("sed config cmd: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 


        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='sed',
                                                        filename=filename,
                                                        regex='s/view_index_dir.*//'
                                                    )  
        

        # cmd = CommandFactory.sed(filename, 's/database_dir.*//', self.need_sudo, self.uid)
        # logger.debug("sed config cmd: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='sed',
                                                        filename=filename,
                                                        regex='s/database_dir.*//'
                                                    )  

        # cmd = CommandFactory.change_permission(filename, self.need_sudo, self.uid)
        # logger.debug("chmod config cmd: {}".format(cmd))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd) 

        command_output, std_err, exit_code = self.run_os_command(
                                                        os_command='change_permission',
                                                        path=filename
                                                    )  


    def ignore_err(self, input):
        return True


    def rename_cluster(self):
        """Rename cluster based on user entries"""
        try:


            command_output, std_err, exit_code = self.run_couchbase_command(
                                                    couchbase_command='rename_cluster',
                                                    username=self.snapshot.couchbase_admin,
                                                    password=self.snapshot.couchbase_admin_password,
                                                    newuser=self.parameters.couchbase_admin,
                                                    newpass=self.parameters.couchbase_admin_password,
                                                    newname=self.parameters.tgt_cluster_name
                                                )

            # command = CommandFactory.rename_cluster(self.repository.cb_shell_path, 
            #                                         self.connection.environment.host.name,
            #                                         self.parameters.couchbase_port, 
            #                                         self.snapshot.couchbase_admin,
            #                                         self.parameters.couchbase_admin,
            #                                         self.parameters.tgt_cluster_name)
            # logger.debug("Rename command is {}".format(command))
            # kwargs = {
            #     ENV_VAR_KEY: {
            #         'password': self.snapshot.couchbase_admin_password,
            #         'newpass': self.parameters.couchbase_admin_password
            #     }
            # }
            # server_info, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
            logger.debug(command_output)

        except Exception as error:
            # add error handling
            raise


    def start_node_bootstrap(self):
        self.start_couchbase(no_wait=True)
        end_time = time.time() + 3660
        server_status = Status.INACTIVE

        #break the loop either end_time is exceeding from 1 minute or server is successfully started
        while time.time() < end_time and server_status<>Status.ACTIVE:
            helper_lib.sleepForSecond(1) # waiting for 1 second
            server_status = self.staging_bootstrap_status() # fetching status
            logger.debug("server status {}".format(server_status))



    def addnode(self, nodeno, node_def):
        logger.debug("Adding a node")


        self.delete_config()

        self.start_node_bootstrap()

        self.node_init(nodeno)


        helper_lib.sleepForSecond(10)

        services = [ 'data', 'index', 'query' ]

        if "fts_service" in node_def and node_def["fts_service"] == True:
            services.append('fts')

        if "eventing_service" in node_def and node_def["eventing_service"] == True:
            services.append('eventing')

        if "analytics_service" in node_def and node_def["analytics_service"] == True:
            services.append('analytics')

        logger.debug("services to add: {}".format(services))


        hostip_command = CommandFactory.get_ip_of_hostname()
        logger.debug("host ip command: {}".format(hostip_command))
        host_ip_output, std_err, exit_code = utilities.execute_bash(self.connection, hostip_command)
        logger.debug("host ip Output {} ".format(host_ip_output))


        command_output, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='server_add',
                                                hostname=self.connection.environment.host.name,
                                                newhost=host_ip_output,
                                                services=','.join(services)
                                             )

        # kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # command = CommandFactory.server_add(self.repository.cb_shell_path, 
        #                                     self.connection.environment.host.name,
        #                                     self.parameters.couchbase_port, 
        #                                     self.parameters.couchbase_admin, 
        #                                     host_ip_output,
        #                                     ','.join(services))
        # logger.debug("add node command: {}".format(command))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)

        logger.debug("Add node Output {} ".format(command_output))

        command_output, std_err, exit_code = self.run_couchbase_command(
                                                couchbase_command='rebalance',
                                                hostname=self.connection.environment.host.name
                                             )

        # kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # command = CommandFactory.rebalance(self.repository.cb_shell_path, 
        #                                     self.connection.environment.host.name,
        #                                     self.parameters.couchbase_port, 
        #                                     self.parameters.couchbase_admin)
        # logger.debug("rebalancd command: {}".format(command))
        # command_output, std_err, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
        logger.debug("Rebalance Output {} ".format(command_output))

        

        # /opt/couchbase/bin/couchbase-cli node-init -c marcincoucheetgt2.dcol1.delphix.com:8091 -u slon -p slonslon -d --node-init-data-path /mnt/provision/slonik/data2 --node-init-index-path /mnt/provision/slonik/data2 --node-init-analytics-path /mnt/provision/slonik/data2 --node-init-eventing-path /mnt/provision/slonik/data2
        # /opt/couchbase/bin/couchbase-cli server-add -c marcincoucheetgt.dcol1.delphix.com:8091 -u slon -p slonslon -d --server-add http://marcincoucheetgt2.dcol1.delphix.com:8091 --server-add-username slon --server-add-password slonslon --services data,analytics
        # /opt/couchbase/bin/couchbase-cli rebalance -c marcincoucheetgt.dcol1.delphix.com:8091 -u slon -p slonslon --no-progress-bar


if __name__ == "__main__":
    print "Checking Couchbase Class"
    test_object = CouchbaseOperation(Resource.ObjectBuilder.set_dsource(True).build())
    print (test_object.get_config_file_path.__doc__)
