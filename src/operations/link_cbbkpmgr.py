#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################
# In this module, functions defined for couchbase backup manager ingestion mechanism.
#######################################################################################################################

import logging
import os
import json

from dlpx.virtualization.platform import Status

import db_commands.constants
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.helper_lib import get_bucket_size_in_MB, get_sync_lock_file_name
from controller.resource_builder import Resource
from generated.definitions import SnapshotDefinition
from internal_exceptions.plugin_exceptions import MultipleSyncError, MultipleSnapSyncError
from operations import config
from operations import linking

logger = logging.getLogger(__name__)


def resync_cbbkpmgr(staged_source, repository, source_config, input_parameters):
    dsource_type = input_parameters.d_source_type
    dsource_name = source_config.pretty_name
    couchbase_host = input_parameters.couchbase_host
    bucket_size = staged_source.parameters.bucket_size
    rx_connection = staged_source.staged_connection
    resync_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())


    linking.check_for_concurrent(resync_process, dsource_type, dsource_name, couchbase_host)

    # validate if this works as well for backup
    linking.configure_cluster(resync_process)


    logger.debug("Finding source and staging bucket list")
    bucket_details_source = resync_process.source_bucket_list_offline()
    bucket_details_staged = helper_lib.filter_bucket_name_from_output(resync_process.bucket_list())

    buckets_toprocess = linking.buckets_precreation(resync_process, bucket_details_source, bucket_details_staged)

    csv_bucket_list = ",".join(buckets_toprocess)
    logger.debug("Started CB backup manager")
    helper_lib.sleepForSecond(30)
    resync_process.cb_backup_full(csv_bucket_list)
    helper_lib.sleepForSecond(30)

    linking.build_indexes(resync_process)
    logger.info("Stopping Couchbase")
    resync_process.stop_couchbase()
    resync_process.save_config('parent')

def pre_snapshot_cbbkpmgr(staged_source, repository, source_config, input_parameters):


    # this is for normal snapshot
    #logger.info("Do nothing version  Couchbase")

    pre_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    bucket_size = input_parameters.bucket_size
    rx_connection = staged_source.staged_connection

    dsource_type = input_parameters.d_source_type
    dsource_name = source_config.pretty_name
    couchbase_host = input_parameters.couchbase_host
    linking.check_for_concurrent(pre_snapshot_process, dsource_type, dsource_name, couchbase_host)

    logger.debug("Finding source and staging bucket list")
    bucket_details_source = pre_snapshot_process.source_bucket_list_offline()
    bucket_details_staged = helper_lib.filter_bucket_name_from_output(pre_snapshot_process.bucket_list())

    bucket_details_staged = pre_snapshot_process.bucket_list()
    filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
    csv_bucket_list = ",".join(filter_bucket_list)
    pre_snapshot_process.cb_backup_full(csv_bucket_list)
    logger.info("Re-ingesting from latest backup complete.")

    linking.build_indexes(pre_snapshot_process)
    logger.info("Stopping Couchbase")
    pre_snapshot_process.stop_couchbase()
    pre_snapshot_process.save_config('parent')


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

    # if len(staged_source.parameters.config_settings_prov) != 0:
    #     bucket_list = []
    #     for config_setting in staged_source.parameters.config_settings_prov:
    #         bucket_list.append(helper_lib.get_bucket_name_with_size(bucket_details, config_setting["bucketName"]))
    # else:
    #     bucket_list = helper_lib.get_stg_all_bucket_list_with_ramquota_size(bucket_details)


    # extract index

    ind = post_snapshot_process.get_indexes_definition()
    logger.debug("indexes definition : {}".format(ind))

    snapshot.indexes = ind
    snapshot.db_path = staged_source.parameters.mount_path
    snapshot.couchbase_port = source_config.couchbase_src_port
    snapshot.couchbase_host = source_config.couchbase_src_host
    snapshot.bucket_list = json.dumps(bucket_details)
    snapshot.time_stamp = helper_lib.current_time()
    snapshot.snapshot_id = str(helper_lib.get_snapshot_id())
    snapshot.couchbase_admin = post_snapshot_process.parameters.couchbase_admin
    snapshot.couchbase_admin_password = post_snapshot_process.parameters.couchbase_admin_password
    #logger.debug("snapshot schema: {}".format(snapshot))
    logger.debug("Deleting the lock files")
    helper_lib.delete_file(rx_connection, config.SNAP_SYNC_FILE_NAME)
    helper_lib.delete_file(rx_connection, config.SYNC_FILE_NAME)
    # for Prox investigation
    #post_snapshot_process.stop_couchbase()
    #helper_lib.unmount_file_system(rx_connection, staged_source.parameters.mount_path)
    #logger.debug("Un mounting completed")
    return snapshot


def start_staging_cbbkpmgr(staged_source, repository, source_config):
    start_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())

    start_staging.delete_config()
    # TODO error handling
    start_staging.restore_config(what='current')
    start_staging.start_couchbase()


def stop_staging_cbbkpmgr(staged_source, repository, source_config):
    stop_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    stop_staging.stop_couchbase()
    stop_staging.save_config(what='current')
    stop_staging.delete_config()


def d_source_status_cbbkpmgr(staged_source, repository, source_config):
    # if helper_lib.check_dir_present(staged_source.staged_connection, staged_source.parameters.couchbase_bak_loc):
    #     return Status.ACTIVE
    # return Status.INACTIVE
    status_obj = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source).set_repository(repository).set_source_config(
            source_config).build())
    logger.debug("Checking status for D_SOURCE: {}".format(source_config.pretty_name))
    return status_obj.status()



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

