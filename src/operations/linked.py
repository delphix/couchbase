#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

import logging
import os
from dlpx.virtualization.platform import Status

from plugin_internal_exceptions.plugin_exception import  handle_error_response
from generated.definitions import SnapshotDefinition
from controller.internal_couchbase_library.couchbase_operation import CouchbaseProcess
from controller import helper_lib
import db_commands_data.constants_variables
from plugin_internal_exceptions.base_exception import Response

logger = logging.getLogger(__name__)

SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = True
SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = True


# @handle_plugin_exception(ResyncFailedError)
def resync(staged_source, repository, source_config, input_parameters):
    logger.debug("In Re-sync...")
    helper_lib.print_sign("#")

    dsource_type = input_parameters.d_source_type
    bucket_size = input_parameters.bucket_size
    eviction_policy = input_parameters.bucket_eviction_policy
    dsource_name = source_config.pretty_name
    rx_connection = staged_source.staged_connection
    global SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED

    resync_process = CouchbaseProcess(staged_source=staged_source,
                                      repository = repository,
                                      source_config = source_config)

    config_dir = resync_process.create_config_dir()
    sync_filename = config_dir + "/" + _get_sync_file_name(dsource_type, dsource_name)
    src_bucket_info_filename = db_commands_data.constants_variables.SRC_BUCKET_INFO_FILENAME
    src_bucket_info_filename = os.path.dirname(config_dir) + "/" + src_bucket_info_filename
    logger.debug("src_bucket_info_filename = {}".format(src_bucket_info_filename))

    try:
        if dsource_type == "Couchbase Backup Manager" and helper_lib.check_file_present(rx_connection, sync_filename) :
            logger.debug("Sync file is already created by other process")
            SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED =False
            _get_response_for_sync_file(sync_filename)
        elif dsource_type == "XDCR" and not _verify_sync_lock_file_for_this_job(rx_connection, sync_filename):
            SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
            logger.debug("Sync file is already created by other dSource")
            _get_response_for_sync_file_for_XDCR(sync_filename)
        else:
            #creating sync  file
            msg = "dSource Creation / Snapsync for dSource {} is in progress. Same staging server {} cannot be used for other operations".format(dsource_name,input_parameters.couchbase_host)
            helper_lib.write_file(rx_connection, msg, sync_filename )

        resync_process.restart_couchbase()
        resync_process.node_init()
        resync_process.cluster_init()

        if dsource_type == "XDCR":
            already_set_up_done, name_conflict = resync_process.check_duplicate_cluster(resync_process.parameters.stg_cluster_name)
            if already_set_up_done:
                logger.info("No need to XDCR setup again")
            elif name_conflict:
                raise Exception(Response("", "Cluster with given name already exist",
                                         "Delete existing staging cluster configuration on source or use different staging cluster name"))
            else :
                logger.info("Initiating first time XDCR set up")
                resync_process.xdcr_setup()

        #common steps for both XDCR & CB back up
        logger.debug("Finding source and staging bucket list")
        if dsource_type == "XDCR":
            bucket_details_source = resync_process.source_bucket_list()
        else:
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
                bkt_name_size =helper_lib.get_bucket_name_with_size(bucket_details_source, config_bucket["bucketName"])
                bkt_size_mb = _get_bucket_size_in_MB(bucket_size, bkt_name_size.split(",")[1])

                if config_bucket["bucketName"] not in bucket_details_staged:
                    resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
                else:
                    logger.debug("Bucket {} already present in staged environment. Recreating bucket ".format(config_bucket["bucketName"]))
                    resync_process.bucket_remove( config_bucket["bucketName"])
                    resync_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)

                if dsource_type == "XDCR":
                    resync_process.xdcr_replicate( config_bucket["bucketName"],config_bucket["bucketName"])

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
                if(items is not None or items != ""):
                    logger.debug("Running bucket operations for {}".format(items))
                    bkt_name,bkt_size = items.split(',')

                    bkt_size_mb = _get_bucket_size_in_MB(bucket_size, bkt_size)
                    if(bkt_name not in bucket_details_staged):
                        logger.debug("Creating bucket {}".format(bkt_name))
                        resync_process.bucket_create( bkt_name, bkt_size_mb)
                    else:
                        logger.debug("Bucket {} already present in staged environment. Recreating bucket ".format(bkt_name))
                        resync_process.bucket_remove(bkt_name)
                        resync_process.bucket_create(bkt_name, bkt_size_mb)

                    if dsource_type == "XDCR":
                        resync_process.xdcr_replicate( bkt_name, bkt_name)

            bucket_details_staged = resync_process.bucket_list()
            filter_staged_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
            extra_bucket = list(set(filter_staged_bucket) - set(filter_source_bucket))
            logger.info("Extra bucket found to delete:{}".format(extra_bucket))
            for bucket in extra_bucket:
                resync_process.bucket_remove( bucket)

        if dsource_type == "XDCR":
            logger.debug("Finding staging_uuid & cluster_name on staging")
            staging_uuid, cluster_name_staging = resync_process.get_replication_uuid()
            bucket_details_staged = resync_process.bucket_list()
            logger.debug("Filtering bucket name from output")
            filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
            for bkt in filter_bucket_list:
                resync_process.monitor_bucket(bkt,staging_uuid)

        elif dsource_type == "Couchbase Backup Manager":
            bucket_details_staged = resync_process.bucket_list()
            filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
            csv_bucket_list = ",".join(filter_bucket_list)
            logger.debug("Started CB backup manager")
            resync_process.cb_backup_full(csv_bucket_list)

    except Exception as Error:
        logger.debug("Caught exception {}".format(Error.message))
        if SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            _cleanup_in_exception_case(rx_connection, sync_filename)
        else:
            logger.debug(
                "Not cleaning lock files as not created by this job. Also check, is there any XDCR set up on this host. If yes then sync file should not be deleted")
        handle_error_response(Error,"Resynchronization is Failed. ")
    logger.info("Completed resynchronization Operation")

# @handle_plugin_exception(Exception)
def pre_snapshot(staged_source, repository, source_config, input_parameters):
    logger.info("In Pre snapshot...")
    pre_snapshot_process = CouchbaseProcess(staged_source=staged_source,
                                      repository = repository,
                                      source_config = source_config)

    dsource_type = input_parameters.d_source_type
    bucket_size = input_parameters.bucket_size
    eviction_policy = input_parameters.bucket_eviction_policy
    dsource_name = source_config.pretty_name
    rx_connection = staged_source.staged_connection

    config_dir = pre_snapshot_process.create_config_dir()
    sync_filename = config_dir + "/" + _get_sync_file_name(dsource_type, dsource_name)

    snapsync_filename = db_commands_data.constants_variables.LOCK_SNAPSYNC_OPERATION
    snapsync_filename = config_dir + "/"+ snapsync_filename

    src_bucket_info_filename = db_commands_data.constants_variables.SRC_BUCKET_INFO_FILENAME
    src_bucket_info_filename = os.path.dirname(config_dir) + "/" + src_bucket_info_filename

    logger.debug("set sync filename = {}".format(sync_filename))
    logger.debug("set snap-sync filename = {}".format(snapsync_filename))
    logger.debug("src_bucket_info_filename = {}".format(src_bucket_info_filename))
    global SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED
    global SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED

    try:
        if dsource_type == "Couchbase Backup Manager":
            #Check if sync_filename snapsync.lck is presnet

            if not helper_lib.check_file_present(rx_connection, sync_filename):
                logger.debug("Sync File is not present {}, which is expected".format(sync_filename))
                if helper_lib.check_file_present(rx_connection, snapsync_filename):
                    logger.debug("File path is already created {}".format(snapsync_filename))
                    SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED =False
                    _get_response_for_snap_sync_file(snapsync_filename)
                else:
                    logger.debug("Creating lock file...")
                    msg = "dSource Creation / Snapsync for dSource {} is in progress. Same staging server {} cannot be used for other operations".format(dsource_name,input_parameters.couchbase_host)
                    helper_lib.write_file(rx_connection, msg, snapsync_filename )
                    # Put intellegence to ingest only if file is new. Validate with timestamp of folder.
                    logger.debug("Re-ingesting from latest backup...")
                    pre_snapshot_process.start_couchbase()
                    pre_snapshot_process.node_init()
                    pre_snapshot_process.cluster_init()
                    #bucket_details_source = pre_snapshot_process.source_bucket_list()
                    bucket_details_source = pre_snapshot_process.source_bucket_list_offline(filename=src_bucket_info_filename)
                    bucket_details_staged = pre_snapshot_process.bucket_list()
                    config_setting = staged_source.parameters.config_settings_prov
                    logger.debug("Buckets name passed for configuration: {}".format(config_setting))
                    bucket_configured_staged = []
                    if len(config_setting) != 0:
                        logger.debug("Inside config")
                        for config_bucket in config_setting:
                            logger.debug("Adding bucket names provided in config settings")
                            bucket_configured_staged.append(config_bucket["bucketName"])
                            bkt_name_size =helper_lib.get_bucket_name_with_size(bucket_details_source, config_bucket["bucketName"])
                            bkt_size_mb = _get_bucket_size_in_MB(bucket_size, bkt_name_size.split(",")[1])

                            if config_bucket["bucketName"] not in bucket_details_staged:
                                pre_snapshot_process.bucket_create(config_bucket["bucketName"], bkt_size_mb)
                            else:
                                pre_snapshot_process.bucket_remove( config_bucket["bucketName"])
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
                            if(items is not None or items != ""):
                                bkt_name,bkt_size = items.split(',')
                                bkt_size_mb = _get_bucket_size_in_MB(bucket_size, bkt_size)
                                if(bkt_name not in bucket_details_staged):
                                    pre_snapshot_process.bucket_create( bkt_name, bkt_size_mb)
                                else:
                                    logger.info("Bucket {} already present in staged environment. Recreating bucket ".format(bkt_name))
                                    pre_snapshot_process.bucket_remove(bkt_name)
                                    pre_snapshot_process.bucket_create(bkt_name, bkt_size_mb)

                        bucket_details_staged = pre_snapshot_process.bucket_list()
                        filter_staged_bucket = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
                        extra_bucket = list(set(filter_staged_bucket) - set(filter_source_bucket))
                        logger.info("Extra bucket found :{}".format(extra_bucket))
                        for bucket in extra_bucket:
                            pre_snapshot_process.bucket_remove( bucket)

                    bucket_details_staged = pre_snapshot_process.bucket_list()
                    filter_bucket_list = helper_lib.filter_bucket_name_from_output(bucket_details_staged)
                    csv_bucket_list = ",".join(filter_bucket_list)
                    pre_snapshot_process.cb_backup_full(csv_bucket_list)
                    logger.info("Re-ingesting from latest backup complete.")

        elif dsource_type == "XDCR":
            # Dont care of sync.lck file as it will never de deleted even in post snapshot.
            if helper_lib.check_file_present(rx_connection, snapsync_filename):
                SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
                _get_response_for_snap_sync_file(snapsync_filename)
            else:
                logger.debug("Creating lock file...")
                msg = "dSource Creation / Snapsync for dSource {} is in progress. Same staging server {} cannot be used for other operations".format(dsource_name,input_parameters.couchbase_host)
                helper_lib.write_file(rx_connection, msg, snapsync_filename )

        index_script_data = pre_snapshot_process.generate_index_script()
        file_path = staged_source.parameters.mount_path+"/"+ db_commands_data.constants_variables.INDEX_SCRIPT
        helper_lib.write_file(rx_connection, index_script_data, file_path)
        logger.info("Stopping Couchbase")
        pre_snapshot_process.stop_couchbase()

    except Exception as Error:
        logger.debug("Caught exception : {}".format(Error.message))
        if SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            _cleanup_in_exception_case(rx_connection, None, snapsync_filename)
        if SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            _cleanup_in_exception_case(rx_connection, sync_filename, None)
        if not SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED or not SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            logger.debug("Not cleaning lock files as not created by this job. Also check, is there any XDCR set up on this host. If yes then sync file should not be deleted")
        handle_error_response(Error, "Pre-snapshot operation is failed. ")


# @handle_plugin_exception(PostSnapshotFailedError)
def post_snapshot(staged_source, repository, source_config, dsource_type):
    logger.info("In Post snapshot...")
    post_snapshot_process = CouchbaseProcess(staged_source=staged_source,
                                      repository = repository,
                                      source_config = source_config)
    dsource_name = source_config.pretty_name
    rx_connection = staged_source.staged_connection

    config_dir = post_snapshot_process.create_config_dir()
    sync_filename = config_dir + "/" + _get_sync_file_name(dsource_type, dsource_name)
    snapsync_filename = db_commands_data.constants_variables.LOCK_SNAPSYNC_OPERATION
    snapsync_filename = config_dir + "/"+ snapsync_filename
    global SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED
    global SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED

    try:
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

        snapshot.db_path  = staged_source.parameters.mount_path
        snapshot.couchbase_port = source_config.couchbase_src_port
        snapshot.couchbase_host = source_config.couchbase_src_host
        snapshot.bucket_list = ":".join(bucket_list)
        snapshot.time_stamp = helper_lib.current_time()
        snapshot.snapshot_id = str(helper_lib.get_snapshot_id())
        logger.debug("snapshot schema: {}".format(snapshot))
        logger.debug("Deleting the lock files")

        helper_lib.delete_file(rx_connection, snapsync_filename)
        if dsource_type == "Couchbase Backup Manager":
            helper_lib.delete_file(rx_connection,sync_filename)
            post_snapshot_process.stop_couchbase()
            logger.debug("Un mounting file system")
            helper_lib.unmount_file_system(rx_connection, staged_source.parameters.mount_path)
            logger.debug("Un mounting completed")

        return snapshot
    except Exception as Error:
        logger.debug("Caught exception in post snapshot: {}".format(Error.message))
        if SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            _cleanup_in_exception_case(rx_connection, None, snapsync_filename)
        if SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED and dsource_type == "Couchbase Backup Manager":
            _cleanup_in_exception_case(rx_connection, sync_filename, None)
        if not SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED or not SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED:
            logger.debug(
                "Not cleaning lock files as not created by this job. Also check, is there any XDCR set up on this host. If yes then sync file should not be deleted")
        handle_error_response(Error, "Post-snapshot operation is failed. ")


# @handle_plugin_exception(EnableFailedError)
def start_staging(staged_source, repository, source_config):
    start_staging = CouchbaseProcess(staged_source=staged_source,
                                             repository=repository,
                                             source_config=source_config)

    logger.debug("Enabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection

    start_staging.start_couchbase()
    try:
        if dsource_type == "XDCR":
            logger.info("Initiating first time XDCR set up")
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
                    start_staging.xdcr_replicate( bkt_name, bkt_name)

            config_dir = start_staging.create_config_dir()
            msg = "dSource Creation / Snapsync for dSource {} is in progress".format(source_config.pretty_name)
            helper_lib.write_file(rx_connection, msg, config_dir + "/" + _get_sync_file_name(dsource_type, source_config.pretty_name) )
        logger.debug("D_SOURCE:{} enabled".format(source_config.pretty_name))
    except Exception as Error:
        handle_error_response(Error, "Enable operation is failed. ")


# @handle_plugin_exception(DisableFailedError)
def stop_staging(staged_source, repository, source_config):

    stop_staging = CouchbaseProcess(staged_source=staged_source,
                                     repository=repository,
                                     source_config=source_config)

    logger.debug("Disabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection
    try:
        if dsource_type == "XDCR":
            logger.info("Deleting Existing Replication")
            is_xdcr_setup, cluster_name = stop_staging.delete_replication()
            if (is_xdcr_setup):
                logger.info("Deleting XDCR")
                stop_staging.xdcr_delete(cluster_name)
            config_dir = stop_staging.create_config_dir()
            helper_lib.delete_file(rx_connection, config_dir+"/"+_get_sync_file_name(dsource_type, source_config.pretty_name))

    except Exception as Error:
        handle_error_response(Error, "Disable operation is failed. ")
    stop_staging.stop_couchbase()
    logger.debug("D_SOURCE:{} disabled".format(source_config.pretty_name))


# @handle_plugin_exception(StatusFailedError)
def d_source_status(staged_source, repository, source_config):
    status_obj = CouchbaseProcess(staged_source=staged_source,
                                     repository=repository,
                                     source_config=source_config)
    logger.debug("Checking status for D_SOURCE: {}".format( source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    if dsource_type == "Couchbase Backup Manager":
        if helper_lib.check_dir_present(staged_source.staged_connection, staged_source.parameters.couchbase_bak_loc):
            return Status.ACTIVE
        return Status.INACTIVE
    else:
        return status_obj.status()

def _get_response_for_sync_file_for_XDCR(sync_filename):
    logger.debug("Getting error response object for sync failure")
    response = Response()
    response.std_output = "Multiple XDCR is not supported on single staging host"
    response.message = "XDCR setup found on staging host"
    response.possible_actions = "Please use different staging host"
    raise Exception(response)

def _get_response_for_sync_file(sync_filename):
    logger.debug("Getting error response object for sync failure")
    response = Response()
    response.std_output = "Staging host already in use. Only Serial operations supported for couchbase. File {} exists".format(sync_filename)
    response.message = "Resynchronization is already running for other dSource"
    response.possible_actions = "Please wait while the other operation completes and try again "
    raise Exception(response)

def _get_response_for_snap_sync_file(snap_sync_filename):
    logger.debug("Getting error response object for snap sync failure")
    response = Response()
    response.std_output = "Staging host already in use for snapsync. Only Serial operations supported for couchbase. File {} exists".format(snap_sync_filename)
    response.message = "SnapSync is running for any other dSource"
    response.possible_actions = "Please wait while the other operation completes and try again "
    raise Exception(response)

def _cleanup_in_exception_case(rx_connection, sync_filename=None,snap_sync_filename=None ):
    if sync_filename:
        helper_lib.delete_file(rx_connection, sync_filename)
    if snap_sync_filename:
        helper_lib.delete_file(rx_connection, snap_sync_filename)


def _get_sync_file_name(dsource_type, dsource_name):
    sync_filename = db_commands_data.constants_variables.LOCK_SYNC_OPERATION
    if dsource_type == "XDCR":
        striped_dsource_name = dsource_name.replace(" ", "")
        sync_filename = str(striped_dsource_name)+str(sync_filename)
    return sync_filename

def _verify_sync_lock_file_for_this_job(rx_connection, sync_filename):
    logger.debug("Checking for {}".format(sync_filename))
    if helper_lib.check_file_present(rx_connection, sync_filename):
        return True
    config_dir = os.path.dirname(sync_filename)

    possible_sync_filename = "/*"+db_commands_data.constants_variables.LOCK_SYNC_OPERATION
    possible_sync_filename = config_dir + possible_sync_filename
    logger.debug("Checking for {}".format(possible_sync_filename))
    if helper_lib.check_file_present(rx_connection, possible_sync_filename):
        return False
    return True

def _get_bucket_size_in_MB(bucket_size, bkt_name_size):
    bkt_size_mb = 0
    if bucket_size > 0:
        bkt_size_mb = bucket_size
    else:
        bkt_size_mb = int(bkt_name_size) // 1024 // 1024
    logger.debug("bkt_size_mb : {}".format(bkt_size_mb))
    return bkt_size_mb