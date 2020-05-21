#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
 This class contains methods for all bucket related operations .This is child class of Resource and parent class
 of CouchbaseOperation
"""
#######################################################################################################################
import logging
from utils import utilities
import json
from internal_exceptions.database_exceptions import BucketOperationError
from controller import helper_lib
from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.resource_builder import Resource
from db_commands.commands import CommandFactory
from db_commands.constants import ENV_VAR_KEY, EVICTION_POLICY

logger = logging.getLogger(__name__)


class _BucketMixin(Resource, MixinInterface):

    def __init__(self, builder):
        super(_BucketMixin, self).__init__(builder)

    def bucket_edit(self, bucket_name, flush_value=1):
        """
        Edit a bucket settings
        :param bucket_name: bucket name to edit
        :param flush_value: It decides the edit mode. It could be 0 or 1.
        :return:None
        """
        # It requires the before bucket delete
        logger.debug("Editing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_edit(bucket_name=bucket_name, flush_value=flush_value, **env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        return utilities.execute_bash(self.connection, command, **kwargs)

    def bucket_edit_ramquota(self, bucket_name, _ramsize):
        """
        :param bucket_name: Required bucket_name on which edit operation will run
        :param _ramsize:
        :return:
        """
        # It requires the before bucket delete
        logger.debug("Editing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_edit_ramquota(bucket_name=bucket_name, ramsize=_ramsize, **env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        return utilities.execute_bash(self.connection, command, **kwargs)

    def bucket_delete(self, bucket_name):
        # To delete the bucket
        logger.debug("Deleting bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_delete(bucket_name=bucket_name, **env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        return utilities.execute_bash(self.connection, command, **kwargs)

    def bucket_flush(self, bucket_name):
        # It requires the before bucket delete
        logger.debug("Flushing bucket: {} ".format(bucket_name))
        self.__validate_bucket_name(bucket_name)
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_flush(bucket_name=bucket_name, **env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        return utilities.execute_bash(self.connection, command, **kwargs)

    def bucket_remove(self, bucket_name):
        logger.debug("Removing bucket: {} ".format(bucket_name))
        self.bucket_edit(bucket_name, flush_value=1)
        self.bucket_flush(bucket_name)
        self.bucket_edit(bucket_name, flush_value=0)
        self.bucket_delete(bucket_name)
        helper_lib.sleepForSecond(2)

    def bucket_create(self, bucket_name, ram_size=0):
        logger.debug("Creating bucket: {} ".format(bucket_name))
        # To create the bucket with given ram size
        self.__validate_bucket_name(bucket_name)
        if ram_size is None:
            logger.debug("Needed ramsize for bucket_create. Currently it is: {}".format(ram_size))
            return
        policy = self.parameters.bucket_eviction_policy
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_create(bucket_name=bucket_name, ramsize=ram_size, evictionpolicy=policy, **env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        output, error, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
        helper_lib.sleepForSecond(2)

    def bucket_list(self, return_type=list):
        # See the all bucket. It will return also other information like ramused, ramsize etc
        logger.debug("Finding staged bucket list")
        env = _BucketMixin.generate_environment_map(self)
        command = CommandFactory.bucket_list(**env)
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        bucket_list, error, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
        if return_type == list:
            bucket_list = bucket_list.split("\n")
        logger.debug("Bucket details in staged environment: {}".format(bucket_list))
        return bucket_list

    def monitor_bucket(self, bucket_name, staging_UUID):
        # To monitor the replication
        logger.debug("Monitoring the replication for bucket {} ".format(bucket_name))
        kwargs = {ENV_VAR_KEY: {'password': self.staged_source.parameters.xdcr_admin_password}}
        command = CommandFactory.monitor_replication(source_username=self.staged_source.parameters.xdcr_admin,
                                                     source_hostname=self.source_config.couchbase_src_host,
                                                     source_port=self.source_config.couchbase_src_port,
                                                     bucket_name=bucket_name, uuid=staging_UUID)
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
        logger.debug("stdout: {}".format(stdout))
        content = json.loads(stdout)
        pending_docs = self._get_last_value_of_node_stats(content["nodeStats"].values()[0])
        while pending_docs != 0:
            logger.debug("Documents pending for replication: {}".format(pending_docs))
            helper_lib.sleepForSecond(30)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, command, **kwargs)
            content = json.loads(stdout)
            pending_docs = self._get_last_value_of_node_stats(content["nodeStats"].values()[0])
        else:
            logger.debug("Replication for bucket {} completed".format(bucket_name))

    @staticmethod
    def _get_last_value_of_node_stats(content_list):
        """
        :param content_list:
        :return: last node value, if the list is defined. it the list is empty return 0
        """
        value = 0
        if len(content_list) > 0:
            value = content_list[-1]

        logger.debug("Current node-stats value is: {}".format(value))
        return value

    @staticmethod
    def __validate_bucket_name(name):
        # Validate bucket name is empty or valid value
        if name is None or name == "":
            logger.debug("Invalid bucket name {}".format(name))
            raise BucketOperationError("Bucket not found ")

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {'shell_path': self.repository.cb_shell_path, 'hostname': self.connection.environment.host.name,
               'port': self.parameters.couchbase_port, 'username': self.parameters.couchbase_admin}
        # MixinInterface.read_map(env)
        return env
