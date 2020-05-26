#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################
"""
This class contains methods for replication related operations
This is child class of Resource and parent class of CouchbaseOperation
"""
#######################################################################################################################

from utils import utilities
import re
import logging
from db_commands.commands import CommandFactory
from controller.couchbase_lib._mixin_interface import MixinInterface
from db_commands.constants import ENV_VAR_KEY
from controller.resource_builder import Resource
logger = logging.getLogger(__name__)


class _ReplicationMixin(Resource, MixinInterface):

    def __init__(self, builder):
        super(_ReplicationMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {'shell_path': self.repository.cb_shell_path, 'source_hostname': self.source_config.couchbase_src_host,
               'source_port': self.source_config.couchbase_src_port, 'source_username': self.parameters.xdcr_admin}
        # MixinInterface.read_map(env)
        return env

    def get_replication_uuid(self):
        # False for string
        logger.debug("Finding the replication uuid through host name")
        is_ip_or_string = False
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        cluster_name = self.parameters.stg_cluster_name
        env = _ReplicationMixin.generate_environment_map(self)
        cmd = CommandFactory.get_replication_uuid(**env)
        try:

            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
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
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        uuid, cluster_name = self.get_replication_uuid()
        if uuid is None:
            return None, None
        env = _ReplicationMixin.generate_environment_map(self)
        cmd = CommandFactory.get_stream_id(cluster_name=cluster_name, **env)
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
        if stdout is None or stdout == "":
            logger.debug("No stream ID identified")
            return None, None
        else:
            stream_id = re.findall(r"(?<=stream id: ){}.*".format(uuid), stdout)
            logger.debug("Stream id found: {}".format(stream_id))
            return stream_id, cluster_name

    def pause_replication(self):
        logger.debug("Pausing replication ...")
        stream_id, cluster_name = self.get_stream_id()
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        env = _ReplicationMixin.generate_environment_map(self)
        for replication_id in stream_id:
            cmd = CommandFactory.pause_replication(cluster_name=cluster_name, id=replication_id, **env)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
            logger.debug(stdout)

    def resume_replication(self):
        logger.debug("Resuming replication ...")
        stream_id, cluster_name = self.get_stream_id()
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        env = _ReplicationMixin.generate_environment_map(self)
        for s_id in stream_id:
            cmd = CommandFactory.resume_replication(cluster_name=cluster_name, id=s_id , **env)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
            logger.debug(stdout)

    def delete_replication(self):
        logger.debug("Deleting replication...")
        stream_id, cluster_name = self.get_stream_id()
        logger.debug("stream_id: {} and cluster_name : {}".format(stream_id, cluster_name))
        if stream_id is None or stream_id == "":
            logger.debug("No Replication is found to delete.")
            return False, cluster_name
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        env = _ReplicationMixin.generate_environment_map(self)

        for id in stream_id:
            cmd = CommandFactory.delete_replication(cluster_name=cluster_name, id=id, **env)
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
            if exit_code != 0:
                logger.warn("stream_id: {} deletion failed".format(id))
            else:
                logger.debug("stream_id: {} deletion succeeded".format(id))
        return True, cluster_name

    def get_ip(self):
        cmd = CommandFactory.get_ip_of_hostname()
        stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd)
        logger.debug("IP is  {}".format(stdout))
        return stdout

    def check_duplicate_replication(self, cluster_name):
        logger.debug("Searching cluster name")
        kwargs = {ENV_VAR_KEY: {'source_password': self.parameters.xdcr_admin_password}}
        env = _ReplicationMixin.generate_environment_map(self)
        cmd = CommandFactory.get_replication_uuid(**env)
        try:
            stdout, stderr, exit_code = utilities.execute_bash(self.connection, cmd, **kwargs)
            all_clusters = re.findall(r'cluster name:.*', stdout)
            stream_id, cluster = self.get_stream_id()
            logger.debug("stream_id:{} and cluster s:{} ".format(stream_id, cluster))
            if stream_id:
                # cluster is already set up between these nodes# No setup and no mis match
                logger.debug("Already XDCR set up have been between source and staging server")
                return True, False
            logger.debug("No XDCR for staging host. Now validating the cluster name... ")
            for each_cluster_pair in all_clusters:
                each_cluster = each_cluster_pair.split(':')[1].strip()
                logger.debug("Listed cluster: {} and input is:{} ".format(each_cluster, cluster_name))
                if each_cluster == cluster_name:
                    logger.debug("Duplicate cluster name issue identified ")
                    # no setup but mismatch
                    return False, True
            return False, False

        except Exception as err:
            logger.debug("Failed to verify the duplicate name: {} ".format(err.message))
