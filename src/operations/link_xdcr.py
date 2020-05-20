#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################
# In this module, functions defined for XDCR ingestion mechanism
#######################################################################################################################

import logging
import os

from generated.definitions import SnapshotDefinition
import db_commands.constants
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.resource_builder import Resource
from generated.definitions import SnapshotDefinition
from internal_exceptions.database_exceptions import DuplicateClusterError
from internal_exceptions.plugin_exceptions import MultipleSyncError, MultipleXDCRSyncError
from operations import config

logger = logging.getLogger(__name__)


def resync_xdcr(staged_source, repository, source_config, input_parameters):
    dsource_type = input_parameters.d_source_type
    dsource_name = source_config.pretty_name
    bucket_size = staged_source.parameters.bucket_size
    rx_connection = staged_source.staged_connection
    resync_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    config_dir = resync_process.create_config_dir()
    config.SYNC_FILE_NAME = config_dir + "/" + helper_lib.get_sync_lock_file_name(dsource_type, dsource_name)


    if not verify_sync_lock_file_for_this_job(rx_connection, config.SYNC_FILE_NAME):
        config.SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
        logger.debug("Sync file is already created by other dSource")
        raise MultipleXDCRSyncError("Sync file is already created by other dSource")
    else:
        # creating sync  file
        msg = db_commands.constants.RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS.format(dsource_name,
                                                                                            input_parameters.couchbase_host)
        helper_lib.write_file(rx_connection, msg, config.SYNC_FILE_NAME)

    resync_process.restart_couchbase()
    resync_process.node_init()
    resync_process.cluster_init()
    already_set_up_done, name_conflict = resync_process.check_duplicate_replication(
        resync_process.parameters.stg_cluster_name)
    if already_set_up_done:
        logger.info("No need to XDCR setup again")
    elif name_conflict:
        raise DuplicateClusterError("Already cluster is present")
    else:
        logger.info("First time XDCR set up")
        resync_process.xdcr_setup()
    # common steps for both XDCR & CB back up
    logger.debug("Finding source and staging bucket list")
    bucket_details_source = resync_process.source_bucket_list()
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
            bkt_size_mb = helper_lib.get_bucket_size_in_MB(bucket_size, bkt_name_size.split(",")[1])

            if config_bucket["bucketName"] not in bucket_details_staged:
                resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
            else:
                logger.debug("Bucket {} already present in staged environment. Recreating bucket ".format(
                    config_bucket["bucketName"]))
                resync_process.bucket_remove(config_bucket["bucketName"])
                resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
            resync_process.xdcr_replicate(config_bucket["bucketName"], config_bucket["bucketName"])

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

                bkt_size_mb = helper_lib.get_bucket_size_in_MB(bucket_size, bkt_size)
                if bkt_name not in bucket_details_staged:
                    resync_process.bucket_create(bkt_name, bkt_size_mb)
                else:
                    logger.debug(
                        "Bucket {} already present in staged environment. Recreating bucket ".format(bkt_name))
                    resync_process.bucket_remove(bkt_name)
                    resync_process.bucket_create(bkt_name, bkt_size_mb)
                resync_process.xdcr_replicate(bkt_name, bkt_name)

        bucket_details_staged = resync_process.bucket_list()
        filter_staged_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
        extra_bucket = list(set(filter_staged_bucket) - set(filter_source_bucket))
        logger.info("Extra bucket found to delete:{}".format(extra_bucket))
        for bucket in extra_bucket:
            resync_process.bucket_remove(bucket)

    logger.debug("Finding staging_uuid & cluster_name on staging")
    staging_uuid, cluster_name_staging = resync_process.get_replication_uuid()
    bucket_details_staged = resync_process.bucket_list()
    logger.debug("Filtering bucket name from output")
    filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
    for bkt in filter_bucket_list:
        resync_process.monitor_bucket(bkt, staging_uuid)


def pre_snapshot_xdcr(staged_source, repository, source_config, input_parameters):
    logger.info("In Pre snapshot...")
    pre_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    config.SNAP_SYNC_FILE_NAME = pre_snapshot_process.create_config_dir() + "/" + db_commands.constants.LOCK_SNAPSYNC_OPERATION
    # Don't care of sync.lck file as it will never de deleted even in post snapshot.
    if helper_lib.check_file_present(staged_source.staged_connection,  config.SNAP_SYNC_FILE_NAME):
        config.SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
        raise MultipleSyncError()
    else:
        logger.debug("Creating lock file...")
        msg = db_commands.constants.RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS.format(source_config.pretty_name,
                                                                                            input_parameters.couchbase_host)
        helper_lib.write_file(staged_source.staged_connection, msg,  config.SNAP_SYNC_FILE_NAME)
    logger.info("Stopping Couchbase")
    pre_snapshot_process.stop_couchbase()


def post_snapshot_xdcr(staged_source, repository, source_config, dsource_type):
    logger.info("In Post snapshot...")
    post_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())

    post_snapshot_process.start_couchbase()
    snapshot = SnapshotDefinition(validate=False)
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
    logger.debug("Deleting the snap sync lock file {}".format(config.SNAP_SYNC_FILE_NAME))
    helper_lib.delete_file(staged_source.staged_connection, config.SNAP_SYNC_FILE_NAME)
    return snapshot


def start_staging_xdcr(staged_source, repository, source_config):
    start_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())

    logger.debug("Enabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection
    start_staging.start_couchbase()

    already_set_up_done, name_conflict = start_staging.check_duplicate_replication(
        start_staging.parameters.stg_cluster_name)
    if already_set_up_done:
        logger.info("No need to XDCR setup again")
    elif name_conflict:
        raise DuplicateClusterError("Already cluster is present")
    else:
        logger.info("First time XDCR set up")
        start_staging.xdcr_setup()

    config_setting = staged_source.parameters.config_settings_prov

    if len(config_setting) > 0:
        for config_bucket in config_setting:
            logger.debug("Creating replication for {}".format(config_bucket["bucketName"]))
            start_staging.xdcr_replicate(config_bucket["bucketName"], config_bucket["bucketName"])
    else:
        bucket_details_source = start_staging.source_bucket_list()
        all_bkt_list_with_size = helper_lib.get_all_bucket_list_with_size(bucket_details_source)
        for items in all_bkt_list_with_size:
            bkt_name, bkt_size = items.split(',')
            logger.debug("Creating replication for {}".format(bkt_name))
            start_staging.xdcr_replicate(bkt_name, bkt_name)

        config_dir = start_staging.create_config_dir()
        msg = "dSource Creation / Snapsync for dSource {} is in progress".format(source_config.pretty_name)
        helper_lib.write_file(rx_connection, msg,
                              config_dir + "/" + helper_lib.get_sync_lock_file_name(dsource_type,
                                                                                    source_config.pretty_name))
    logger.debug("D_SOURCE:{} enabled".format(source_config.pretty_name))


def stop_staging_xdcr(staged_source, repository, source_config):
    stop_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())

    logger.debug("Disabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection
    logger.info("Deleting Existing Replication")
    is_xdcr_setup, cluster_name = stop_staging.delete_replication()
    if is_xdcr_setup:
        logger.info("Deleting XDCR")
        stop_staging.xdcr_delete(cluster_name)
    config_dir = stop_staging.create_config_dir()
    helper_lib.delete_file(rx_connection,
                           config_dir + "/" + helper_lib.get_sync_lock_file_name(dsource_type,
                                                                                 source_config.pretty_name))
    stop_staging.stop_couchbase()
    logger.debug("D_SOURCE:{} disabled".format(source_config.pretty_name))


def d_source_status_xdcr(staged_source, repository, source_config):
    status_obj = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    logger.debug("Checking status for D_SOURCE: {}".format(source_config.pretty_name))
    return status_obj.status()


def verify_sync_lock_file_for_this_job(rx_connection, sync_filename):
    if helper_lib.check_file_present(rx_connection, sync_filename):
        logger.debug("Sync File Present: {}".format(sync_filename))
        return True
    config_dir = os.path.dirname(sync_filename)

    possible_sync_filename = "/*" + db_commands.constants.LOCK_SYNC_OPERATION
    possible_sync_filename = config_dir + possible_sync_filename
    logger.debug("Checking for {}".format(possible_sync_filename))
    if helper_lib.check_file_present(rx_connection, possible_sync_filename):
        return False
    return True
