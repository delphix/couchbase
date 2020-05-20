#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################
# In this module, all dSource related operations are implemented.
#######################################################################################################################

import logging
import sys

import config
import db_commands
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.resource_builder import Resource
from controller.helper_lib import delete_file
from db_commands import constants
from internal_exceptions.base_exceptions import PluginException, DatabaseException, GenericUserError
from internal_exceptions.plugin_exceptions import MountPathError
from operations import link_cbbkpmgr, link_xdcr

logger = logging.getLogger(__name__)


def resync(staged_source, repository, source_config, input_parameters):
    logger.debug("Started ReSync...")
    try:
        if input_parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.resync_cbbkpmgr(staged_source, repository, source_config, input_parameters)
        elif input_parameters.d_source_type == constants.XDCR:
            link_xdcr.resync_xdcr(staged_source, repository, source_config, input_parameters)
    except Exception as ex_obj:
        logger.debug("Caught exception {}".format(ex_obj.message))
        _cleanup_in_exception_case(staged_source.staged_connection, True, False)
        if input_parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.unmount_file_system_in_error_case(staged_source, repository, source_config)
        if isinstance(ex_obj, PluginException) or isinstance(ex_obj, DatabaseException) or isinstance(ex_obj, GenericUserError):
            raise ex_obj.to_user_error(), None, sys.exc_info()[2]
        raise
    logger.debug("Completed resynchronization")


def pre_snapshot(staged_source, repository, source_config, input_parameters):
    logger.info("In Pre snapshot...")
    try:
        if input_parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.pre_snapshot_cbbkpmgr(staged_source, repository, source_config, input_parameters)
        elif input_parameters.d_source_type == constants.XDCR:
            link_xdcr.pre_snapshot_xdcr(staged_source, repository, source_config, input_parameters)
    except Exception as ex_obj:
        logger.debug("Caught exception: {}".format(ex_obj.message))
        _cleanup_in_exception_case(staged_source.staged_connection, True, True)
        if input_parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.unmount_file_system_in_error_case(staged_source, repository, source_config)
        if isinstance(ex_obj, PluginException) or isinstance(ex_obj, DatabaseException) or isinstance(ex_obj, GenericUserError):
            raise ex_obj.to_user_error(), None, sys.exc_info()[2]
        raise
    logger.debug("Completed Pre-snapshot")


def post_snapshot(staged_source, repository, source_config, dsource_type):
    logger.info("In Post snapshot...")
    try:
        if dsource_type == constants.CBBKPMGR:
            return link_cbbkpmgr.post_snapshot_cbbkpmgr(staged_source, repository, source_config, dsource_type)
        elif dsource_type == constants.XDCR:
            return link_xdcr.post_snapshot_xdcr(staged_source, repository, source_config, dsource_type)
    except Exception as err:
        logger.debug("Caught exception in post snapshot: {}".format(err.message))
        _cleanup_in_exception_case(staged_source.staged_connection, True, True)
        if dsource_type == constants.CBBKPMGR:
            link_cbbkpmgr.unmount_file_system_in_error_case(staged_source, repository, source_config)
        raise
    logger.debug("Completed Post-snapshot")


def start_staging(staged_source, repository, source_config):
    logger.debug("Enabling the D_SOURCE:{}".format(source_config.pretty_name))
    try:
        if staged_source.parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.start_staging_cbbkpmgr(staged_source, repository, source_config)
        elif staged_source.parameters.d_source_type == constants.XDCR:
            link_xdcr.start_staging_xdcr(staged_source, repository, source_config)
    except Exception as err:
        logger.debug("Enable operation is failed!" + err.message)
        raise


def stop_staging(staged_source, repository, source_config):
    logger.debug("Disabling the D_SOURCE:{}".format(source_config.pretty_name))
    try:
        if staged_source.parameters.d_source_type == constants.CBBKPMGR:
            link_cbbkpmgr.stop_staging_cbbkpmgr(staged_source, repository, source_config)
        elif staged_source.parameters.d_source_type == constants.XDCR:
            link_xdcr.stop_staging_xdcr(staged_source, repository, source_config)
    except Exception as err:
        logger.debug("Disable operation is failed!" + err.message)
        raise
    logger.debug("D_SOURCE:{} disabled".format(source_config.pretty_name))


def d_source_status(staged_source, repository, source_config):
    if staged_source.parameters.d_source_type == constants.CBBKPMGR:
        return link_cbbkpmgr.d_source_status_cbbkpmgr(staged_source, repository, source_config)
    elif staged_source.parameters.d_source_type == constants.XDCR:
        return link_xdcr.d_source_status_xdcr(staged_source, repository, source_config)


#This function verifies that LOCK_SNAPSYNC_OPERATION or LOCK_SYNC_OPERATION is present in hidden folder or not
#If any file is present then it will raise exception
#This function does not cover the case for XDCR sync file presence.
def check_mount_path(staged_source, repository):
    mount_path_check = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).build())
    snapsync_filename = mount_path_check.create_config_dir() + "/" + db_commands.constants.LOCK_SNAPSYNC_OPERATION
    sync_filename = mount_path_check.create_config_dir() + "/" + db_commands.constants.LOCK_SYNC_OPERATION
    if helper_lib.check_file_present(staged_source.staged_connection, snapsync_filename) :
        raise MountPathError("Another Snap-Sync process is in progress ").to_user_error(), None, sys.exc_info()[2]
    if helper_lib.check_file_present(staged_source.staged_connection, sync_filename):
        raise MountPathError("Another Sync process is in progress ").to_user_error(), None, sys.exc_info()[2]
    return True


# Below are specific functions for this module only

def _cleanup_in_exception_case(rx_connection, is_sync, is_snap_sync):
    logger.debug("In clean up")
    try:
        if is_snap_sync and config.SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            delete_file(rx_connection, config.SNAP_SYNC_FILE_NAME)
        if is_sync and config.SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            delete_file(rx_connection, config.SYNC_FILE_NAME)
        if not config.SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED or \
                not config.SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            logger.debug(constants.ALREADY_SYNC_FILE_PRESENT_ON_HOST)
    except Exception as err :
        logger.debug("Failed to clean up the lock files {}".format(err.message))
        raise
