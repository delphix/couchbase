#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#

from dlpx.virtualization.platform import Mount, MountSpecification, Plugin, Status
from dlpx.virtualization.platform import OwnershipSpecification
from operations import discovery, linked, virtual
from utils import setup_logger
from db_commands.constants import EVICTION_POLICY
import logging


plugin = Plugin()
setup_logger._setup_logger()

logger = logging.getLogger(__name__)

#
# Below is an example of the repository discovery operation.
#
# NOTE: The decorators are defined on the 'plugin' object created above.
#
# Mark the function below as the operation that does repository discovery.
@plugin.discovery.repository()
def repository_discovery(source_connection):
    #
    # This is an object generated from the repositoryDefinition schema.
    # In order to use it locally you must run the 'build -g' command provided
    # by the SDK tools from the plugin's root directory.
    #
    return discovery.find_repos(source_connection)


@plugin.discovery.source_config()
def source_config_discovery(source_connection, repository):
    #
    # To have automatic discovery of source configs, return a list of
    # SourceConfigDefinitions similar to the list of
    # RepositoryDefinitions above.
    #
    return discovery.find_source(source_connection, repository)


@plugin.linked.post_snapshot()
def linked_post_snapshot(staged_source, repository, source_config, snapshot_parameters):
    return linked.post_snapshot(staged_source, repository, source_config,staged_source.parameters.d_source_type)


@plugin.linked.mount_specification()
def linked_mount_specification(staged_source, repository):
    mount_path = staged_source.parameters.mount_path
    environment = staged_source.staged_connection.environment
    linked.check_mount_path(staged_source, repository)
    logger.debug("Mounting path {}".format(mount_path))
    mounts = [Mount(environment, mount_path)]
    logger.debug("Setting ownership to uid {} and gid {}".format(repository.uid, repository.gid))
    ownership_spec = OwnershipSpecification(repository.uid, repository.gid)
    return MountSpecification(mounts, ownership_spec)


@plugin.linked.pre_snapshot()
def linked_pre_snapshot(staged_source, repository, source_config, snapshot_parameters):
    if int(snapshot_parameters.resync) == 1:
        linked.resync(staged_source, repository, source_config, staged_source.parameters)
    else:
        linked.pre_snapshot(staged_source, repository, source_config, staged_source.parameters)


@plugin.linked.status()
def linked_status(staged_source, repository, source_config):
    return linked.d_source_status(staged_source, repository, source_config)

@plugin.linked.stop_staging()
def stop_staging(staged_source, repository, source_config):
    linked.stop_staging(staged_source, repository, source_config)


@plugin.linked.start_staging()
def start_staging(staged_source, repository, source_config):
    linked.start_staging(staged_source, repository, source_config)


@plugin.virtual.configure()
def configure(virtual_source, snapshot, repository):
    return virtual.vdb_configure(virtual_source, snapshot, repository)


@plugin.virtual.reconfigure()
def reconfigure(virtual_source, repository, source_config, snapshot):
    return virtual.vdb_reconfigure(virtual_source, repository, source_config, snapshot)


@plugin.virtual.pre_snapshot()
def virtual_pre_snapshot(virtual_source, repository, source_config):
    virtual.vdb_pre_snapshot(virtual_source, repository, source_config)


@plugin.virtual.post_snapshot()
def virtual_post_snapshot(virtual_source, repository, source_config):
    return virtual.post_snapshot(virtual_source, repository, source_config)


@plugin.virtual.start()
def start(virtual_source, repository, source_config):
    virtual.vdb_start(virtual_source, repository, source_config)


@plugin.virtual.stop()
def stop(virtual_source, repository, source_config):
    virtual.vdb_stop(virtual_source, repository, source_config)


@plugin.virtual.mount_specification()
def virtual_mount_specification(virtual_source, repository):
    mount_path = virtual_source.parameters.mount_path
    mounts = [Mount(virtual_source.connection.environment, mount_path)]
    logger.debug("Mounting path {}".format(mount_path))
    logger.debug("Setting ownership to uid {} and gid {}".format(repository.uid, repository.gid))
    ownership_spec = OwnershipSpecification(repository.uid, repository.gid)
    return MountSpecification(mounts, ownership_spec)


@plugin.virtual.status()
def virtual_status(virtual_source, repository, source_config):
    return virtual.vdb_status(virtual_source, repository, source_config)


@plugin.virtual.unconfigure()
def unconfigure(virtual_source, repository, source_config):
    logger.debug("UNCONFIGURE")
    virtual.vdb_unconfigure(virtual_source, repository, source_config)
