#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
This module contains the methods responsible for discovery operations.
"""
#######################################################################################################################
import logging
import sys

from controller import helper_lib
from generated.definitions import RepositoryDefinition
from internal_exceptions.base_exceptions import GenericUserError
from internal_exceptions.plugin_exceptions import RepositoryDiscoveryError, SourceConfigDiscoveryError

logger = logging.getLogger(__name__)


def find_repos(source_connection):
    """
    Args:
        source_connection (RemoteConnection): The connection associated with the remote environment to run repository discovery
    Returns:
        Object of RepositoryDefinition class
    """
    try:
        binary_paths = helper_lib.find_binary_path(source_connection)
        repositories = []
        for binary_path in binary_paths.split(';'):
            if helper_lib.check_dir_present(source_connection, binary_path):
                install_path = helper_lib.find_install_path(source_connection, binary_path)
                shell_path = helper_lib.find_shell_path(source_connection, binary_path)
                version = helper_lib.find_version(source_connection, install_path)
                (uid, gid) = helper_lib.find_ids(source_connection, install_path)
                pretty_name = "Couchbase ({})".format(version)
                repository_definition = RepositoryDefinition(cb_install_path=install_path, cb_shell_path=shell_path,
                                                             version=version, pretty_name=pretty_name, uid=uid, gid=gid)
                repositories.append(repository_definition)

        return repositories
    except RepositoryDiscoveryError as err:
        raise err.to_user_error()(None).with_traceback(sys.exc_info()[2])
    except Exception as err:
        logger.debug("find_repos: Caught unexpected exception!" + str(err))
        raise


def find_source(source_connection, repository):
    """
    Args:
        source_connection (RemoteConnection): The connection associated with the remote environment to run repository discovery
        repository:  Object of RepositoryDefinition

    Returns:
        Object of SourceConfigDefinition class.
    """
    logger.debug("Finding source config...")
    try:
        instance = helper_lib.is_instance_present_of_gosecrets(source_connection)
        if not instance:
            logger.debug("No Couchbase instance found on host")
            logger.debug("Hostname: {}".format(source_connection.environment.host.name))
            return []
        else:
            logger.debug("Couchbase instance found on host")
            logger.debug("Hostname: {}".format(source_connection.environment.host.name))
            return []
            # # We don't want to run code beyond this point to avoid showing existing couchbase instance.
            # # Couchbase supports only 1 instance on server so that instance on host should be managed by delphix
            # source_configs = []
            # PORT = 8091
            # pretty_name = "Couchbase:{}".format(PORT)
            # hostname = source_connection.environment.host.name
            # data_path = helper_lib.get_data_directory(source_connection,repository)
            # data_path = os.path.join(data_path, "data")
            # source_config = SourceConfigDefinition(couchbase_src_port=PORT, couchbase_src_host=hostname, pretty_name=pretty_name, db_path=data_path)
            # source_configs.append(source_config)
            # return source_configs
    except SourceConfigDiscoveryError as err:
        raise err.to_user_error()(None).with_traceback(sys.exc_info()[2])
    except Exception as err:
        logger.debug("find_source: Caught unexpected exception!" + str(err))
        raise
