#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################
# In this module, functions defined for couchbase backup manager ingestion mechanism.
#######################################################################################################################

import logging
import os

from dlpx.virtualization.platform import Status

import db_commands.constants
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.helper_lib import get_bucket_size_in_MB, get_sync_lock_file_name
from controller.resource_builder import Resource
from generated.definitions import SnapshotDefinition
from internal_exceptions.plugin_exceptions import MultipleSyncError, MultipleSnapSyncError
from operations import config

logger = logging.getLogger(__name__)


def resync_cbbkpmgr(staged_source, repository, source_config, input_parameters):
    dsource_type = input_parameters.d_source_type
    bucket_size = staged_source.parameters.bucket_size
    rx_connection = staged_source.staged_connection
    resync_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())

    config_dir = resync_process.create_config_dir()
    config.SYNC_FILE_NAME = config_dir + "/" + get_sync_lock_file_name(dsource_type, source_config.pretty_name)
    src_bucket_info_filename = db_commands.constants.SRC_BUCKET_INFO_FILENAME
    src_bucket_info_filename = os.path.dirname(config_dir) + "/" + src_bucket_info_filename
    logger.debug("src_bucket_info_filename = {}".format(src_bucket_info_filename))

    if helper_lib.check_file_present(rx_connection, config.SYNC_FILE_NAME):
        logger.debug("Sync file is already created by other process")
        config.SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
        raise MultipleSyncError("Sync file is already created by other process")
    else:
        # creating sync  file
        msg = db_commands.constants.RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS.format(source_config.pretty_name,
                                                                                            input_parameters.couchbase_host)
        helper_lib.write_file(rx_connection, msg, config.SYNC_FILE_NAME)

    resync_process.restart_couchbase()
    resync_process.node_init()
    resync_process.cluster_init()
    logger.debug("Finding source and staging bucket list")
    bucket_details_source = resync_process.source_bucket_list_offline(filename=src_bucket_info_filename)
    bucket_details_staged = resync_process.bucket_list()

    config_setting = staged_source.parameters.config_settings_prov
    logger.debug("Bucket names passed for configuration: {}".format(config_setting))

    bucket_configured_staged = []
    if len(config_setting) > 0:
        logger.debug("Getting bucket information from config")
        for config_bucket in config_setting:
            bucket_configured_staged.append(config_bucket["bucketName"])
            logger.debug("Filtering bucket name with size only from above output")
            bkt_name_size = helper_lib.get_bucket_name_with_size(bucket_details_source, config_bucket["bucketName"])
            bkt_size_mb = get_bucket_size_in_MB(bucket_size, bkt_name_size.split(",")[1])

            if config_bucket["bucketName"] not in bucket_details_staged:
                resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
            else:
                logger.debug("Bucket {} already present in staged environment. Recreating bucket ".format(
                    config_bucket["bucketName"]))
                resync_process.bucket_remove(config_bucket["bucketName"])
                resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)

        logger.debug("Finding buckets present at staged server")
        bucket_details_staged = resync_process.bucket_list()
        filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
        extra_bucket = list(set(filter_bucket_list) - set(bucket_configured_staged))

        logger.debug("Extra bucket found to delete:{} ".format(extra_bucket))
        for bucket in extra_bucket:
            resync_process.bucket_remove(bucket)
    else:
        logger.debug("Finding buckets present at staged server with size")
        all_bkt_list_with_size = helper_lib.get_all_bucket_list_with_size(bucket_details_source)
        logger.debug("Filtering bucket name with size only from above output")
        filter_source_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_source)
        for items in all_bkt_list_with_size:
            if items:
                logger.debug("Running bucket operations for {}".format(items))
                bkt_name, bkt_size = items.split(',')

                bkt_size_mb = get_bucket_size_in_MB(bucket_size, bkt_size)
                if bkt_name not in bucket_details_staged:
                    resync_process.bucket_create(bkt_name, bkt_size_mb)
                else:
                    logger.debug(
                        "Bucket {} already present in staged environment. Recreating bucket ".format(bkt_name))
                    resync_process.bucket_remove(bkt_name)
                    resync_process.bucket_create(bkt_name, bkt_size_mb)

        bucket_details_staged = resync_process.bucket_list()
        filter_staged_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
        extra_bucket = list(set(filter_staged_bucket) - set(filter_source_bucket))
        logger.info("Extra bucket found to delete:{}".format(extra_bucket))
        for bucket in extra_bucket:
            resync_process.bucket_remove(bucket)

    bucket_details_staged = resync_process.bucket_list()
    filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
    csv_bucket_list = ",".join(filter_bucket_list)
    logger.debug("Started CB backup manager")
    resync_process.cb_backup_full(csv_bucket_list)


def pre_snapshot_cbbkpmgr(staged_source, repository, source_config, input_parameters):
    pre_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    bucket_size = input_parameters.bucket_size
    rx_connection = staged_source.staged_connection
    config_dir = pre_snapshot_process.create_config_dir()
    config.SNAP_SYNC_FILE_NAME = config_dir + "/" + db_commands.constants.LOCK_SNAPSYNC_OPERATION
    src_bucket_info_filename = db_commands.constants.SRC_BUCKET_INFO_FILENAME
    src_bucket_info_filename = os.path.dirname(config_dir) + "/" + src_bucket_info_filename

    if helper_lib.check_file_present(rx_connection, config.SNAP_SYNC_FILE_NAME):
        logger.debug("File path is already created {}".format(config.SNAP_SYNC_FILE_NAME))
        config.SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
        raise MultipleSnapSyncError("SnapSync file is already created by other process")
    else:
        logger.debug("Creating lock file...")
        msg = "dSource Creation / Snapsync for dSource {} is in progress. Same staging server {} cannot be used for other operations".format(
            source_config.pretty_name, input_parameters.couchbase_host)
        helper_lib.write_file(rx_connection, msg, config.SNAP_SYNC_FILE_NAME)
        logger.debug("Re-ingesting from latest backup...")
        pre_snapshot_process.start_couchbase()
        pre_snapshot_process.node_init()
        pre_snapshot_process.cluster_init()
        bucket_details_source = pre_snapshot_process.source_bucket_list_offline(
            filename=src_bucket_info_filename)
        bucket_details_staged = pre_snapshot_process.bucket_list()
        config_setting = staged_source.parameters.config_settings_prov
        logger.debug("Buckets name passed for configuration: {}".format(config_setting))
        bucket_configured_staged = []
        if len(config_setting) != 0:
            logger.debug("Inside config")
            for config_bucket in config_setting:
                logger.debug("Adding bucket names provided in config settings")
                bucket_configured_staged.append(config_bucket["bucketName"])
                bkt_name_size = helper_lib.get_bucket_name_with_size(bucket_details_source,
                                                                     config_bucket["bucketName"])
                bkt_size_mb = get_bucket_size_in_MB(bucket_size, bkt_name_size.split(",")[1])

                if config_bucket["bucketName"] not in bucket_details_staged:
                    pre_snapshot_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
                else:
                    pre_snapshot_process.bucket_remove(config_bucket["bucketName"])
                    pre_snapshot_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
            bucket_details_staged = pre_snapshot_process.bucket_list()
            filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
            extra_bucket = list(set(filter_bucket_list) - set(bucket_configured_staged))
            logger.debug("Extra bucket found :{}".format(extra_bucket))
            for bucket in extra_bucket:
                logger.debug("Deleting bucket {}".format(bucket))
                pre_snapshot_process.bucket_remove(bucket)
        else:
            all_bkt_list_with_size = helper_lib.get_all_bucket_list_with_size(bucket_details_source)
            filter_source_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_source)
            logger.info("Creating the buckets")
            for items in all_bkt_list_with_size:
                if items:
                    bkt_name, bkt_size = items.split(',')
                    bkt_size_mb = get_bucket_size_in_MB(bucket_size, bkt_size)
                    if bkt_name not in bucket_details_staged:
                        pre_snapshot_process.bucket_create(bkt_name, bkt_size_mb)
                    else:
                        logger.info(
                            "Bucket {} already present in staged environment. Recreating bucket ".format(
                                bkt_name))
                        pre_snapshot_process.bucket_remove(bkt_name)
                        pre_snapshot_process.bucket_create(bkt_name, bkt_size_mb)

            bucket_details_staged = pre_snapshot_process.bucket_list()
            filter_staged_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
            extra_bucket = list(set(filter_staged_bucket) - set(filter_source_bucket))
            logger.info("Extra bucket found :{}".format(extra_bucket))
            for bucket in extra_bucket:
                pre_snapshot_process.bucket_remove(bucket)

        bucket_details_staged = pre_snapshot_process.bucket_list()
        filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
        csv_bucket_list = ",".join(filter_bucket_list)
        pre_snapshot_process.cb_backup_full(csv_bucket_list)
        logger.info("Re-ingesting from latest backup complete.")

    logger.info("Stopping Couchbase")
    pre_snapshot_process.stop_couchbase()


def post_snapshot_cbbkpmgr(staged_source, repository, source_config, dsource_type):
    logger.info("In Post snapshot...")
    post_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    rx_connection = staged_source.staged_connection
    post_snapshot_process.start_couchbase()
    snapshot = SnapshotDefinition(validate=False)
    bucket_list = []
    bucket_details = post_snapshot_process.bucket_list()

    if len(staged_source.parameters.config_settings_prov) != 0:
        bucket_list = []
        for config_setting in staged_source.parameters.config_settings_prov:
            bucket_list.append(helper_lib.get_bucket_name_with_size(bucket_details, config_setting["bucketName"]))
    else:
        bucket_list = helper_lib.get_stg_all_bucket_list_with_ramquota_size(bucket_details)

    snapshot.db_path = staged_source.parameters.mount_path
    snapshot.couchbase_port = source_config.couchbase_src_port
    snapshot.couchbase_host = source_config.couchbase_src_host
    snapshot.bucket_list = ":".join(bucket_list)
    snapshot.time_stamp = helper_lib.current_time()
    snapshot.snapshot_id = str(helper_lib.get_snapshot_id())
    logger.debug("snapshot schema: {}".format(snapshot))
    logger.debug("Deleting the lock files")
    helper_lib.delete_file(rx_connection, config.SNAP_SYNC_FILE_NAME)
    helper_lib.delete_file(rx_connection, config.SYNC_FILE_NAME)
    post_snapshot_process.stop_couchbase()
    helper_lib.unmount_file_system(rx_connection, staged_source.parameters.mount_path)
    logger.debug("Un mounting completed")
    return snapshot


def start_staging_cbbkpmgr(staged_source, repository, source_config):
    start_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    start_staging.start_couchbase()


def stop_staging_cbbkpmgr(staged_source, repository, source_config):
    stop_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    stop_staging.stop_couchbase()


def d_source_status_cbbkpmgr(staged_source, repository, source_config):
    if helper_lib.check_dir_present(staged_source.staged_connection, staged_source.parameters.couchbase_bak_loc):
        return Status.ACTIVE
    return Status.INACTIVE


def unmount_file_system_in_error_case(staged_source, repository, source_config):
    try:
        logger.debug("Un-mounting file system as last operation was not successful")
        obj = CouchbaseOperation(
            Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
                source_config).build())
        obj.stop_couchbase()
        helper_lib.unmount_file_system(staged_source.staged_connection, staged_source.parameters.mount_path)
        logger.debug("Un mounting completed")
    except Exception as err:
        logger.debug("Un-mounting failed, reason: "+err.message)

