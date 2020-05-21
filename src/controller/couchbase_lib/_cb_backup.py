#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""This class contains methods for all cb backup manager.
This is child class of Resource and parent class of CouchbaseOperation
"""
#######################################################################################################################
import logging
from utils import utilities
from controller import helper_lib
from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.resource_builder import Resource
from db_commands.constants import ENV_VAR_KEY
from db_commands.commands import CommandFactory

logger = logging.getLogger(__name__)


class _CBBackupMixin(Resource, MixinInterface):

    def __init__(self, builder):
        super(_CBBackupMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {'base_path': helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path),
               'hostname': self.connection.environment.host.name, 'port': self.parameters.couchbase_port,
               'username': self.parameters.couchbase_admin
               }
        # MixinInterface.read_map(env)
        return env

    # Defined for future updates
    def get_indexes_name(self, index_name):
        logger.debug("Finding indexes....")
        env = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        env = _CBBackupMixin.generate_environment_map(self)
        cmd = CommandFactory.get_indexes_name(**env)
        logger.debug("env detail is : ".format(env))
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)
        logger.debug("Indexes are {}".format(command_output))
        return command_output

    # Defined for future updates
    def build_index(self, index_name):
        logger.debug("Building indexes....")
        env = _CBBackupMixin.generate_environment_map(self)
        cmd = CommandFactory.build_index(index_name=index_name, **env)
        command_output, std_err, exit_code = utilities.execute_bash(self.connection, command_name=cmd, **env)
        logger.debug("command_output is ".format(command_output))
        return command_output

    def cb_backup_full(self, csv_bucket):
        logger.debug("Starting Restore via Backup file...")
        logger.debug("csv_bucket_list: {}".format(csv_bucket))
        kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        env = _CBBackupMixin.generate_environment_map(self)
        cmd = CommandFactory.cb_backup_full(backup_location=self.parameters.couchbase_bak_loc,
                                            csv_bucket_list=csv_bucket,
                                            backup_repo=self.parameters.couchbase_bak_repo, **env)
        utilities.execute_bash(self.connection, cmd, **kwargs)
