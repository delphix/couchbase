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
from dlpx.virtualization.platform.exceptions import UserError

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



    def cb_backup_full(self, csv_bucket):
        logger.debug("Starting Restore via Backup file...")
        logger.debug("csv_bucket_list: {}".format(csv_bucket))

        skip = '--disable-analytics'

        if self.parameters.fts_service != True:
            skip = skip + ' {} {} '.format('--disable-ft-indexes','--disable-ft-alias')

        if self.parameters.eventing_service != True:
            skip = skip + ' {} '.format('--disable-eventing')


        logger.debug("skip backup is set to: {}".format(skip))

        # kwargs = {ENV_VAR_KEY: {'password': self.parameters.couchbase_admin_password}}
        # env = _CBBackupMixin.generate_environment_map(self)
        
        # cmd = CommandFactory.cb_backup_full(backup_location=self.parameters.couchbase_bak_loc,
        #                                     csv_bucket_list=csv_bucket,
        #                                     backup_repo=self.parameters.couchbase_bak_repo, 
        #                                     need_sudo=self.need_sudo, uid=self.uid, 
        #                                     skip=skip,
        #                                     **env)
        # logger.debug("Backup restore: {}".format(cmd))
        # utilities.execute_bash(self.connection, cmd, **kwargs)


        stdout, stderr, exit_code = self.run_couchbase_command(couchbase_command='cb_backup_full',
                                                            backup_location=self.parameters.couchbase_bak_loc,
                                                            csv_bucket_list=csv_bucket,
                                                            backup_repo=self.parameters.couchbase_bak_repo, 
                                                            skip=skip, 
                                                            base_path=helper_lib.get_base_directory_of_given_path(self.repository.cb_shell_path)
                                                        )

        if exit_code != 0:
            raise UserError("Problem with restoring backup using cbbackupmgr", "Check if repo and all privileges are correct",
                            "stdout: {}, stderr: {}, exit_code: {}".format(stdout, stderr, exit_code))
