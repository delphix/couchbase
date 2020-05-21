#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
This class contains methods for XDCR related operations
This is child class of Resource and parent class of CouchbaseOperation
"""
#######################################################################################################################
import logging
from utils import utilities
import re
from controller import helper_lib
from db_commands.commands import CommandFactory
from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.resource_builder import Resource

from db_commands.constants import ENV_VAR_KEY

logger = logging.getLogger(__name__)


class _XDCrMixin(Resource, MixinInterface):

    def __init__(self, builder):
        super(_XDCrMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {'shell_path': self.repository.cb_shell_path,
               'source_hostname': self.source_config.couchbase_src_host,
               'source_port': self.source_config.couchbase_src_port,
               'source_username': self.parameters.xdcr_admin,
               'hostname': self.connection.environment.host.name,
               'port': self.parameters.couchbase_port,
               'username': self.parameters.couchbase_admin
               }
        # MixinInterface.read_map(env)
        return env

    def xdcr_delete(self, cluster_name):
        logger.debug("XDCR deletion for cluster_name {} has started ".format(cluster_name))
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password,
                                'password': self.parameters.couchbase_admin_password}}
        env = _XDCrMixin.generate_environment_map(self)
        cmd = CommandFactory.xdcr_delete(cluster_name=cluster_name, **env)
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
        if exit_code != 0:
            logger.error("XDCR Setup deletion failed")
            if stdout:
                if re.search(r"unable to access the REST API", stdout):
                    raise Exception(stdout)
                elif re.search(r"unknown remote cluster", stdout):
                    raise Exception(stdout)
        else:
            logger.debug("XDCR Setup deletion succeeded")

    def xdcr_setup(self):
        logger.debug("Started XDCR set up ...")
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password,
                                'password': self.parameters.couchbase_admin_password}}
        env = _XDCrMixin.generate_environment_map(self)
        cmd = CommandFactory.xdcr_setup(cluster_name=self.parameters.stg_cluster_name, **env)
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
        helper_lib.sleepForSecond(3)

    def xdcr_replicate(self, src, tgt):
        try:
            logger.debug("Started XDCR replication for bucket {}".format(src))
            kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
            env = _XDCrMixin.generate_environment_map(self)
            cmd = CommandFactory.xdcr_replicate(source_bucket_name=src, target_bucket_name=tgt,
                                                cluster_name=self.parameters.stg_cluster_name, **env)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
            if exit_code != 0:
                logger.debug("XDCR replication create failed")
                raise Exception(stdout)
            logger.debug("{} : XDCR replication create succeeded".format(tgt))
            helper_lib.sleepForSecond(2)
        except Exception as e:
            logger.debug("XDCR error {}".format(e.message))
