#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

import re
import json
import logging
import os

from dlpx.virtualization.platform import Status

from utils import utilities
from controller.internal_couchbase_library.schemaresource import SchemaResource
from plugin_internal_exceptions.couchbase_exception import BucketOperationError, XDCRDeletionError
from controller import helper_lib
from controller.internal_couchbase_library.db_exception_handler_meta import DatabaseExceptionHandlerMeta

logger = logging.getLogger(__name__)

# Not Defined parameters
BucketNameIsNotDefined = None
RamSizeIsNotDefined = None
FlushValueIsNotDefined = None
SourceConfigIsNotDefined = None

# Constants
StatusIsActive = "healthy"  # it shows the status of server is good
DELPHIX_HIDDEN_FOLDER = ".delphix"  # Folder inside which config file will create
CONFIG_FILE_NAME = "config.txt"
ENV_VAR_KEY = 'environment_vars'  # This key is used to pass the passwords as environment parameters

# Error string on which we have to skip without raising the Exception
ALREADY_CLUSTER_INIT = "Cluster is already initialized, use setting-cluster to change settings"

# This class defines methods for all couchbase operations. Commands are defined for each method is defined cbase_command.py
# It is child class of SchemaResource and operates on vsdk parameters holding by SchemaResource class.
# Execution of
#

class CouchbaseProcess(SchemaResource):
    __metaclass__ = DatabaseExceptionHandlerMeta

    def __init__(self, **vsdk_parameter):
        """
        :param vsdk_parameter: All VSDK parameters passing via each operation defined in plugin_runner.py
        """
        # initializing the super class i.e SchemaResource
        super(CouchbaseProcess, self).__init__(**vsdk_parameter)

    def restart_couchbase(self):
        # To restart the couchbase server
        self.stop_couchbase()
        self.start_couchbase()

    def start_couchbase(self):
        # To start the couchbase server
        logger.debug("Starting couchbase services")
        env = {"install_path": self.repository.cb_install_path}
        utilities.execute_bash(self.connection, 'start_couchbase', **env)
        helper_lib.sleepForSecond(10)

    def stop_couchbase(self):
        # To stop the couchbase server
        try:
            logger.debug("Stopping couchbase services")
            env = {"install_path": self.repository.cb_install_path}
            utilities.execute_bash(self.connection, 'stop_couchbase', **env)
            helper_lib.sleepForSecond(2)
        except Exception as err:
            logger.debug("Seems like couchbase service is not running. {}".format(err.message))


    def status(self):
        # Check the server status. Healthy or warmup could be one status if the server is running
        try:
            env = self.__get_environment_common_detail(self.source.parameters)
            env['shell_path'] = self.repository.cb_shell_path
            env['hostname'] = self.connection.environment.host.name
            server_info, std_err, exit_code = utilities.execute_bash(self.connection, command_name='server_info', **env)
            status = helper_lib.get_value_of_key_from_json(server_info, 'status')
            if status.strip() == StatusIsActive:
                logger.debug("Server status is:  {}".format("ACTIVE"))
                return Status.ACTIVE
            else:
                logger.debug("Server status is:  {}".format("INACTIVE"))
                return Status.INACTIVE
        except Exception as error:
            if re.search("Unable to connect to host at", error.message):
                helper_lib.print_exception("Seems like couchbase server is not running, watch carefully if "
                                           "is not being up in few minutes")
                return Status.INACTIVE

    def make_directory(self, directory_path):
        logger.debug("Creating Directory {} ".format(directory_path))
        env = {'directory_path': directory_path}
        utilities.execute_bash(self.connection, command_name='make_directory', **env)
        logger.debug("Changing permission of directory path {}".format(directory_path))
        utilities.execute_bash(self.connection, command_name='change_permission', **env)
        logger.debug("Changed the permission of directory")

    def create_config_dir(self):
        logger.debug("Finding toolkit Path...")
        bin_directory, std_err, exit_code = utilities.execute_bash(self.connection, command_name='get_dlpx_bin')
        logger.debug("Found bin_directory {}".format(bin_directory))
        if bin_directory == None or bin_directory == "" :
            raise Exception("Failed to find the toolkit directory")
        # Toolkit directory tested on linuxx86_64Bit is 6 level below jq path
        loop_var = 6
        while (loop_var):
            bin_directory = os.path.dirname(bin_directory)
            loop_var = loop_var  - 1
        dir_name = bin_directory + "/.delphix"
        logger.debug("Toolkit dir {}".format(dir_name))
        if not helper_lib.check_dir_present(self.connection, dir_name) :
            self.make_directory(dir_name)
        return dir_name


    def bucket_edit(self, bucket_name, flush_value=1):
        # It requires the before bucket delete
        logger.debug("Editing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = self.__get_environment_common_detail(self.source.parameters)
        env['flush_value'] = flush_value
        env['bucket_name'] = bucket_name
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name
        return utilities.execute_bash(self.connection, command_name='bucket_edit', **env)

    def bucket_edit_ramquota(self, bucket_name, ramsize):
        # It requires the before bucket delete
        logger.debug("Editing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = self.__get_environment_common_detail(self.source.parameters)
        env['ramsize'] = ramsize
        env['bucket_name'] = bucket_name
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name
        return utilities.execute_bash(self.connection, command_name='bucket_edit_ramquota', **env)

    def bucket_delete(self, bucket_name):
        # To delete the bucket
        logger.debug("Deleting bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = self.__get_environment_common_detail(self.source.parameters)
        env['bucket_name'] = bucket_name
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name
        return utilities.execute_bash(self.connection, command_name='bucket_delete', **env)

    @staticmethod
    def __validate_bucket_name(name):
        # Validate bucket name is empty or valid value
        if name is None or name == "":
            logger.debug("Invalid bucket name {}".format(name))
            raise BucketOperationError("Bucket not found ")

    def bucket_flush(self, bucket_name):
        # It requires the before bucket delete
        logger.debug("Flushing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = self.__get_environment_common_detail(self.source.parameters)
        env['bucket_name'] = bucket_name
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name

        return utilities.execute_bash(self.connection, command_name='bucket_flush', **env)

    def bucket_remove(self, bucket_name):
        logger.debug("Removing bucket: {} ".format(bucket_name))
        self.bucket_edit(bucket_name)
        self.bucket_flush(bucket_name)
        self.bucket_edit(bucket_name, 0)
        self.bucket_delete(bucket_name)

    def bucket_create(self, bucket_name, ram_size=0):
        logger.debug("Creating bucket: {} ".format(bucket_name))
        # To create the bucket with given ram size
        self.__validate_bucket_name(bucket_name)
        env = self.__get_environment_common_detail(self.source.parameters)
        env['bucket_name'] = bucket_name
        if ram_size is None:
            logger.debug("Needed ramsize for bucket_create. Currently it is: {}".format(ram_size))
            return
        env['ramsize'] = ram_size
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name
        env['evictionpolicy'] = "valueOnly"
        output, error, exit_code = utilities.execute_bash(self.connection, command_name='bucket_create', **env)
        helper_lib.sleepForSecond(2)

    def bucket_list(self, return_type=list):
        # See the all bucket. It will return also other information like ramused, ramsize etc
        logger.debug("Finding staged bucket list")
        env = self.__get_environment_common_detail(self.source.parameters)
        env['shell_path'] = self.repository.cb_shell_path
        env['hostname'] = self.connection.environment.host.name
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name='bucket_list', **env)
        if return_type == list:
            bucket_list = bucket_list.split("\n")

        logger.debug("Bucket details in staged environment: {}".format(bucket_list))
        return bucket_list

    def source_bucket_list(self):
        # See the bucket list on source server
        logger.debug("Collecting bucket list information present on source server ")
        env = {
            'shell_path': self.repository.cb_shell_path,
            'source_hostname': self.source_config.couchbase_src_host,
            'source_port': self.source_config.couchbase_src_port,
            'source_username': self.staged_source.parameters.xdcr_admin,
        }
        env[ENV_VAR_KEY] = {'password': self.staged_source.parameters.xdcr_admin_password}
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name='get_source_bucket_list',
                                                               **env)
        if bucket_list == "" or bucket_list is None:
            return []
        bucket_list = bucket_list.split("\n")
        logger.debug("Source Bucket Information {}".format(bucket_list))
        return bucket_list

    def source_bucket_list_offline(self,filename):
        # See the bucket list on source server
        logger.debug("Reading bucket list information of source server from /home/delphix/couchbase_src_bucket_info.cfg")
        env = {
            'filename': filename
        }
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command_name='read_file',
                                                               **env)
        if bucket_list == "" or bucket_list is None:
            return []
        bucket_list = bucket_list.split("\n")
        logger.debug("Source Bucket Information {}".format(bucket_list))
        return bucket_list

    def monitor_bucket(self, bucket_name, staging_UUID):
        # To monitor the replication
        logger.debug("Monitoring the replication for bucket {} ".format(bucket_name))
        kwargs = {
            "source_hostname": self.source_config.couchbase_src_host,
            "source_port": self.source_config.couchbase_src_port,
            "source_username": self.staged_source.parameters.xdcr_admin,
            "bucket_name": bucket_name,
            "uuid": staging_UUID
        }
        kwargs[ENV_VAR_KEY] = {'password': self.staged_source.parameters.xdcr_admin_password}
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, "monitor_replication", **kwargs)
        logger.debug("stdout: {}".format(stdout))
        content = json.loads(stdout)

        pending_docs = self._get_last_value_of_node_stats(content["nodeStats"].values()[0])
        while pending_docs != 0:
            logger.debug("Documents pending for replication: {}".format(pending_docs))
            helper_lib.sleepForSecond(30)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, "monitor_replication", **kwargs)
            content = json.loads(stdout)
            pending_docs = self._get_last_value_of_node_stats(content["nodeStats"].values()[0])
        else:
            logger.debug("Replication for bucket {} completed".format(bucket_name))

    @staticmethod
    def _get_last_value_of_node_stats(content_list):
        value = 0
        if len(content_list) > 0:
            value = content_list[-1]

        logger.debug("Current nodestats value is : {}".format(value))
        return value


    def node_init(self):
        # To initialize the node
        logger.debug("Initializing the NODE")
        env = self.__get_environment_common_detail(self.source.parameters)
        env['shell_path'] = self.repository.cb_shell_path
        env['mount_path'] = self.source.parameters.mount_path
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name='node_init', **env)
        logger.debug("Command Output {} ".format(command_output))

    def get_config_directory(self):
        # Return the config directory
        config_path = self.source.parameters.mount_path + "/" + DELPHIX_HIDDEN_FOLDER
        logger.debug("Config folder is: {}".format(config_path))
        return config_path

    def get_config_file_path(self):
        # Return config file path
        config_file_path = self.get_config_directory() + "/" + CONFIG_FILE_NAME
        logger.debug("Config filepath is: {}".format(config_file_path))
        return config_file_path

    def cluster_init(self):
        # Cluster initialization
        logger.debug("Cluster Initialization started")
        fts_service = self.source.parameters.fts_service
        analytics_service = self.source.parameters.analytics_service
        eventing_service = self.source.parameters.eventing_service
        kwargs = {
            "shell_path": self.repository.cb_shell_path,
            "hostname": self.connection.environment.host.name,
            "port": self.source.parameters.couchbase_port,
            "username": self.source.parameters.couchbase_admin,
            "cluster_ramsize": self.source.parameters.cluster_ram_size,
            "cluster_index_ramsize": self.source.parameters.cluster_index_ram_size,
            "cluster_fts_ramsize": self.source.parameters.cluster_ftsram_size,
            "cluster_eventing_ramsize": self.source.parameters.cluster_eventing_ram_size,
            "cluster_analytics_ramsize": self.source.parameters.cluster_analytics_ram_size,
        }
        if self.dSource:
            kwargs['cluster_name'] = self.source.parameters.stg_cluster_name
        else:
            kwargs['cluster_name'] = self.source.parameters.tgt_cluster_name

        kwargs[ENV_VAR_KEY] = {'password': self.source.parameters.couchbase_admin_password}

        additional_service = "query"
        if fts_service:
            additional_service = additional_service + ",fts"
        if analytics_service:
            additional_service = additional_service + ",analytics"
        if eventing_service:
            additional_service = additional_service + ",eventing"

        logger.debug("Adding additional services selected : {}".format(additional_service))
        kwargs["additional_services"] = additional_service

        lambda_expr = lambda output: bool(re.search(ALREADY_CLUSTER_INIT, output))

        stdout, stderr, exit_code = utilities.execute_bash(self.connection,  'cluster_init', callback_func=lambda_expr, **kwargs)
        if re.search(r"ERROR", str(stdout)):
            if re.search(r"ERROR: Cluster is already initialized", stdout):
                logger.debug("Performing cluster setting as cluster is already initialized")
                self.cluster_setting()
            else:
                logger.error("Cluster init failed. Throwing exception")
                raise Exception(stdout)
        else:
            logger.debug("Cluster init succeeded")
        return [stdout, stderr, exit_code]

    def cluster_setting(self):
        logger.debug("Cluster setting process has started")
        kwargs = {"shell_path": self.repository.cb_shell_path, "hostname": self.connection.environment.host.name,
                  "port": self.source.parameters.couchbase_port, "username": self.source.parameters.couchbase_admin,
                  "cluster_ramsize": self.source.parameters.cluster_ram_size,
                  "cluster_index_ramsize": self.source.parameters.cluster_index_ram_size,
                  "cluster_fts_ramsize": self.source.parameters.cluster_ftsram_size,
                  "cluster_eventing_ramsize": self.source.parameters.cluster_eventing_ram_size,
                  "cluster_analytics_ramsize": self.source.parameters.cluster_analytics_ram_size,
                  ENV_VAR_KEY: {'password': self.source.parameters.couchbase_admin_password}}
        if self.dSource:
            kwargs['cluster_name'] = self.source.parameters.stg_cluster_name
        else:
            kwargs['cluster_name'] = self.source.parameters.tgt_cluster_name

        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'cluster_setting', **kwargs)
        if re.search(r"ERROR", str(stdout)):
            logger.error("Cluster modification failed, killing the execution")
            raise Exception(stdout)
        logger.debug("Cluster modification succeeded")
        return [stdout, stderr, exit_code]

    def xdcr_setup(self):
        logger.debug("Started XDCR set up ...")
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  "hostname": self.connection.environment.host.name, "port": self.source.parameters.couchbase_port,
                  "username": self.source.parameters.couchbase_admin,
                  "cluster_name": self.source.parameters.stg_cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password,
                                'password': self.source.parameters.couchbase_admin_password}}

        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'xdcr_setup', **kwargs)
        helper_lib.sleepForSecond(3)

    def xdcr_replicate(self, source_bucket_name, target_bucket_name):
        logger.debug("Started XDCR replication for bucket {} ...".format(source_bucket_name))
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin, "source_bucket_name": source_bucket_name,
                  "target_bucket_name": target_bucket_name, "cluster_name": self.source.parameters.stg_cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'xdcr_replicate', **kwargs)
        if exit_code != 0:
            logger.error("XDCR replication create failed")
            raise Exception(stdout)
        else:
            logger.debug("{} : XDCR replication create succeeded".format(kwargs["target_bucket_name"]))
        helper_lib.sleepForSecond(2)

    def get_ip(self):
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'get_ip_of_hostname')
        logger.debug("IP is  {}".format(stdout))
        return stdout

    def get_replication_uuid(self):
        #False for string
        logger.debug("Finding the replication uuid through host name")
        is_ip_or_string = False
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        cluster_name = self.source.parameters.stg_cluster_name

        try:
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'get_replication_uuid', **kwargs)
            if stdout is None or stdout == "":
                logger.debug("No Replication ID identified")
                return None, None
            logger.debug("xdcr remote references : {}".format(stdout))
            hostname = self.connection.environment.host.name
            logger.debug("Environment hostname {}".format(hostname))
            host_ip = ""
            if not re.search(r"{}".format(hostname), stdout):
                logger.debug("cluster for hostname {} doesn't exist".format(hostname))
                logger.debug("Finding the ip for this host")
                host_ip = self.get_ip()
                logger.debug("Finding the replication uuid through host ip")
                if not re.search(r"{}".format(host_ip), stdout):
                    logger.debug("cluster for host_ip {} doesn't exist".format(hostname))
                    return None, None
                else:
                    is_ip_or_string = True
                    logger.debug("cluster for host_ip {} exist".format(host_ip))
            else:
                logger.debug("cluster for hostname {}  exist".format(host_ip))
            if is_ip_or_string == False:
                uuid = re.search(r"uuid:.*(?=\s.*{})".format(hostname), stdout).group()
            else:
                uuid = re.search(r"uuid:.*(?=\s.*{})".format(host_ip), stdout).group()

            uuid = uuid.split(":")[1].strip()
            cluster_name_staging = re.search(r"cluster name:.*(?=\s.*{})".format(uuid), stdout).group()
            cluster_name_staging = cluster_name_staging.split(":")[1].strip()
            logger.debug("uuid for {} cluster : {}".format(uuid, cluster_name_staging))
            if cluster_name_staging == cluster_name:
                return uuid, cluster_name
            else:
                return uuid, cluster_name_staging
        except Exception as err:
            logger.warn("Error identified: {} ".format(err.message))
            logger.warn("UUID is None. Not able to find any cluster")
            return None, None

    def get_stream_id(self):
        logger.debug("Finding the stream id for provided cluster name")
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  "cluster_name": self.source.parameters.stg_cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        uuid, cluster_name = self.get_replication_uuid()
        kwargs["cluster_name"] = cluster_name
        if uuid is None:
            return None, None
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'get_stream_id', **kwargs)
        if stdout is None or stdout == "":
            logger.debug("No stream ID identified")
            return None, None
        else:
            logger.debug("stream id: {}".format(stdout))
            logger.debug("uuid: {}".format(uuid))
            stream_id = re.findall(r"(?<=stream id: ){}.*".format(uuid), stdout)
            logger.debug("Stream id found: {}".format(stream_id))
            return stream_id, cluster_name

    def pause_replication(self):
        logger.debug("Pausing replication ...")
        stream_id, cluster_name = self.get_stream_id()
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin, "cluster_name": cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}

        for replication_id in stream_id:
            kwargs["id"] = replication_id
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'pause_replication', **kwargs)
            logger.debug(stdout)

    def resume_replication(self):
        logger.debug("Resuming replication ...")
        stream_id, cluster_name = self.get_stream_id()
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin, "cluster_name": cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        for id in stream_id:
            kwargs["id"] = id
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'resume_replication', **kwargs)
            logger.debug(stdout)

    def delete_replication(self):
        logger.debug("Deleting replication...")
        stream_id, cluster_name = self.get_stream_id()
        logger.debug("stream_id: {} and cluster_name : {}".format(stream_id,cluster_name))
        if stream_id is None or stream_id == "":
            logger.debug("No Replication is found to delete.")
            return False, cluster_name
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  "cluster_name": cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        for id in stream_id:
            kwargs["id"] = id
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'delete_replication', **kwargs)
            if exit_code != 0:
                logger.warn("stream_id: {} deletion failed".format(id))
            else:
                logger.debug("stream_id: {} deletion succeeded".format(id))
        return True, cluster_name

    def xdcr_delete(self, cluster_name):
        logger.debug("XDCR deletion for cluster_name {} has started ".format(cluster_name))
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  "hostname": self.source.staged_connection.environment.host.name,
                  "port": self.source.parameters.couchbase_port, "username": self.source.parameters.couchbase_admin,
                  "cluster_name": cluster_name,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password,
                                'password': self.source.parameters.couchbase_admin_password}}
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'xdcr_delete', **kwargs)
        if exit_code != 0:
            logger.error("XDCR Setup deletion failed")
            if stdout is not None or stdout != "":
                if re.search(r"unable to access the REST API", stdout):
                    raise Exception(stdout)
                elif re.search(r"unknown remote cluster", stdout):
                    raise Exception(stdout)
        else:
            logger.debug("XDCR Setup deletion succeeded")

    def check_duplicate_cluster(self, cluster_name):
        logger.debug("Searching cluster name")
        kwargs = {"shell_path": self.repository.cb_shell_path, "source_hostname": self.source_config.couchbase_src_host,
                  "source_port": self.source_config.couchbase_src_port,
                  "source_username": self.source.parameters.xdcr_admin,
                  ENV_VAR_KEY: {'source_password': self.source.parameters.xdcr_admin_password}}
        try:
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'get_replication_uuid', **kwargs)
            all_clusters = re.findall(r'cluster name:.*', stdout)
            stream_id, cluster = self.get_stream_id()
            logger.debug("stream_id:{} and cluster s:{} ".format(stream_id, cluster))
            if(stream_id):
                #cluster is already set up between these nodes# No setup and no mis match
                logger.debug("Already XDCR set up have been between source and staging server")
                return True, False
            logger.debug("No XDCR for staging host. Now validating the cluster name... ")
            for each_cluster_pair in all_clusters:
                each_cluster = each_cluster_pair.split(':')[1].strip()
                logger.debug("each_cluster:{} and input is:{} ".format(each_cluster,cluster_name))
                if each_cluster == cluster_name:
                    logger.debug("Duplicate cluster name issue identified ")
                    #no setup but mismatch
                    return False, True
            return False, False




        except Exception as err:
            logger.debug("Failed to verify the duplicate name: {} ".format(err.message))

    # Defined for future updates
    def get_indexes_name(self, index_name):
        logger.debug("Finding indexes....")
        env = {'base_path': helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),
               'hostname': self.connection.environment.host.name, 'port': self.parameters.couchbase_port,
               'username': self.parameters.couchbase_admin, 'index': index_name,
               ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        logger.debug("env detail is : ".format(env))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name='get_indexes_name',
                                                                    **env)
        logger.debug("Indexes are {}".format(command_output))
        return command_output

    # Defined for future updates
    def build_index(self, index_name):
        logger.debug("Building indexes....")
        env = {'base_path': helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path), 'index_name': index_name,
               'hostname': self.connection.environment.host.name}
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name='build_index', **env)
        logger.debug("command_output is ".format(command_output))
        return command_output

    def cb_backup_full(self, csv_bucket_list):
        logger.debug("Starting Restore via Backup file...")
        logger.debug("csv_bucket_list: {}".format(csv_bucket_list))
        env = {'base_path': helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),
               'backup_location': self.parameters.couchbase_bak_loc,
               'backup_repo': self.parameters.couchbase_bak_repo,
               "hostname": self.source.staged_connection.environment.host.name,
               "port": self.parameters.couchbase_port,
               'username': self.parameters.couchbase_admin,
               'csv_bucket_list' : csv_bucket_list,
                ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, 'cb_backup_full', **env)


    @staticmethod
    def __get_environment_common_detail(parameters):
        # Return the port, username & password in env variable.
        # This is common method for most of the functions. It needs parameter object
        env = {'port': parameters.couchbase_port, 'username': parameters.couchbase_admin}
        env[ENV_VAR_KEY] = {'password': parameters.couchbase_admin_password}
        return env
