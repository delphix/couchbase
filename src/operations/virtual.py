#
# Copyright (c) 2020 by Delphix. All rights reserved.
#


# Python packages
import re

# Auto generated libs
from generated.definitions import SnapshotDefinition
from generated.definitions import SourceConfigDefinition

# Internal libs
from plugin_internal_exceptions.couchbase_exception import FailedToReadBucketDataFromSnapshot
from plugin_internal_exceptions.plugin_exception import handle_plugin_exception, StatusFailedError, DisableFailedError, \
    RefreshFailedError, ProvisionFailedError, PostSnapshotFailedError, VDBStopFailedError, VDBStartFailedError, \
    handle_error_response
from controller import helper_lib
from controller.internal_couchbase_library.couchbase_operation import CouchbaseProcess
import logging

# Global logger for this File
logger = logging.getLogger(__name__)

# @handle_plugin_exception(StatusFailedError)
def vdb_status(virtual_source, repository, source_config):
    provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository, source_config=source_config, dSource=False)
    cb_status = provision_process.status()
    logger.debug("VDB Status is {}".format(cb_status))
    return cb_status


# @handle_plugin_exception(DisableFailedError)
def vdb_unconfigure(virtual_source, repository, source_config):
    # delete all buckets
    vdb_stop(virtual_source, repository, source_config)


# @handle_plugin_exception(RefreshFailedError)
def vdb_reconfigure(virtual_source, repository, source_config, snapshot):
    # delete all buckets
    #calll configure
    vdb_start(virtual_source, repository, source_config)
    return _source_config(virtual_source, repository, source_config, snapshot)


# @handle_plugin_exception(ProvisionFailedError)
def vdb_configure(virtual_source, snapshot, repository):
    try:
        provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository, snapshot= snapshot, dSource=False)

        helper_lib.heading(" Starting Couchbase", level='info')
        provision_process.restart_couchbase()
        helper_lib.end_line()

        helper_lib.heading("Step2: Initializing Node", level='info')
        provision_process.node_init()
        helper_lib.end_line()

        helper_lib.heading("Step3: Initializing Cluster", level='info')
        provision_process.cluster_init()
        helper_lib.end_line()

        helper_lib.heading("Step4: Started Provisioning", level='info')
        _do_provision(provision_process, snapshot)
        helper_lib.end_line()

        helper_lib.heading("Step5: Cleaning Buckets", level='info')
        _cleanup(provision_process,snapshot)
        helper_lib.end_line()

        helper_lib.heading("Step6: Snapping the VDB", level='info')
        src_cfg_obj = _source_config(virtual_source, repository, None, snapshot)
        helper_lib.end_line()
        return src_cfg_obj
    except Exception as error:
        handle_error_response(error,"Provision is failed ")


def _do_provision(provision_process, snapshot):
    bucket_list_and_size = snapshot.bucket_list

    if not bucket_list_and_size:
        raise FailedToReadBucketDataFromSnapshot("Snapshot Data is empty.")
    else:
        logger.debug("snapshot bucket data is: {}".format(bucket_list_and_size))

    for item in bucket_list_and_size.split(':'):
        logger.debug("Creating bucket is: {}".format(item))
        # try:
        bucket_name = item.split(',')[0]
        bkt_size_mb = int(item.split(',')[1].strip()) // 1024 // 1024
        provision_process.bucket_create(bucket_name, bkt_size_mb)
        helper_lib.sleepForSecond(2)
        # except Exception as err:
        #     logger.debug("Failed in provisioning operation.")
        #     logger.error("Failed in provisioning operation.")

    try:
        # getting config directory path
        directory = provision_process.get_config_directory()

        # making directory and changing permission to 755.
        provision_process.make_directory(directory)
        # This file path is being used to store the bucket information coming in snapshot
        config_file_path = provision_process.get_config_file_path()

        content = "BUCKET_LIST=" + _find_bucket_name_from_snapshot(snapshot)

        # Adding bucket list in config file path .config file, inside .delphix folder
        helper_lib.write_file(provision_process.connection, content, config_file_path)

    except Exception as err:
        logger.error("Failed to Dump the bucket info in config file with error {}".format(err.message))


def _cleanup(provision_process, snapshot):
    logger.debug("Deleting buckets which is extra for this")
    bucket_list=[]
    # Get details of already exist buckets on the target server. We need to delete if some of these are not needed
    try:
        bucket_list = provision_process.bucket_list()
        logger.debug(bucket_list)
        # Removing extra information captured like ramsize, ramused. Only need to get bucket name from output
        bucket_list = helper_lib.filter_bucket_name_from_output(bucket_list)
    except Exception as err:
        logger.error("Failed to get bucket list")

    snapshot_bucket_list_and_size = snapshot.bucket_list
    snapshot_bucket = _find_bucket_name_from_snapshot(snapshot)

    if (snapshot_bucket):
        logger.debug("BUCKET_LIST to be provisioned: {}".format(snapshot_bucket))
        snapshot_bucket_list = snapshot_bucket.split(':')
        bucket_to_delete = []
        bucket_to_update = []
        for bkt in bucket_list:
            #logger.debug("Checking bkt:  {}".format(bkt))
            if bkt not in snapshot_bucket_list:
                bucket_to_delete.append(bkt)
            else:
                bucket_to_update.append(bkt)

        logger.debug("Bucket list to delete: {} ".format(bucket_to_delete))
        _bucket_common_task(provision_process, bucket_to_delete)
        logger.debug("Bucket list to update: {} ".format(bucket_to_update))
        _bucket_modify_task(provision_process, bucket_to_update,snapshot_bucket_list_and_size)        
    else:
        logger.error("This block is not expected to run")


def _bucket_common_task(provision_process, bucket_list):
    for bkt in bucket_list:
        bkt = bkt.strip()
        logger.debug("Deletion of bucket {} started".format(bkt))
        provision_process.bucket_edit( bkt, flush_value=1)
        provision_process.bucket_flush( bkt)
        provision_process.bucket_edit( bkt, flush_value=0)
        provision_process.bucket_delete( bkt)
        helper_lib.sleepForSecond(2)

def _bucket_modify_task(provision_process, bucket_list,snapshot_bucket_list_and_size):
    #logger.debug("snapshot_bucket_list_and_size = {}".format(snapshot_bucket_list_and_size))
    #logger.debug("bucket_list = {}".format(bucket_list))
    for bkt in bucket_list:
        bkt = bkt.strip()
        logger.debug("Modification of bucket {} started".format(bkt))
        ramquotasize = _find_bucket_size_byname(bkt,snapshot_bucket_list_and_size)
        logger.debug("Update bucket {} with ramsize {}MB".format(bkt,ramquotasize))
        provision_process.bucket_edit_ramquota( bkt, ramsize=ramquotasize)
        helper_lib.sleepForSecond(2)

def _source_config(virtual_source, repository=None, source_config=None, snapshot=None):
    provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository,
                                         source_config=source_config, snapshot=snapshot, dSource=False)
    port = virtual_source.parameters.couchbase_port
    mount_path = virtual_source.parameters.mount_path
    host = virtual_source.connection.environment.host.name
    pretty_name = "Couchbase:" + str(port) + " - " + mount_path
    return SourceConfigDefinition(
        couchbase_src_host=host,
        couchbase_src_port=port,
        pretty_name=pretty_name,
        db_path=mount_path
    )


# @handle_plugin_exception(VDBStartFailedError)
def vdb_start(virtual_source, repository, source_config):
    provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository,
                                         source_config=source_config, dSource=False)

    logger.debug("Starting couchbase server")
    try:
        provision_process.start_couchbase()
    except Exception as error:
        handle_error_response(error, "Failed to start couchbase service ")


# @handle_plugin_exception(VDBStopFailedError)
def vdb_stop(virtual_source, repository, source_config):
    provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository, source_config=source_config, dSource=False)
    logger.debug("Stopping couchbase server")
    provision_process.stop_couchbase()


# @handle_plugin_exception(Exception)
def vdb_pre_snapshot():
    logger.debug("In Pre snapshot...")


# @handle_plugin_exception(PostSnapshotFailedError)
def post_snapshot(virtual_source, repository, source_config):
    try:
        helper_lib.heading("Taking Post Snapshot...")
        provision_process = CouchbaseProcess(virtual_source=virtual_source, repository=repository,
                                             source_config=source_config, dSource=False)
        config_file = provision_process.get_config_file_path()

        stdout, stderr, exit_code = helper_lib.read_file(virtual_source.connection, config_file)
        bucket_list = re.sub('BUCKET_LIST=', '', stdout)
        logger.debug("BUCKET_LIST={}".format(bucket_list))
        db_path = virtual_source.parameters.mount_path
        time_stamp = helper_lib.current_time()
        couchbase_port = virtual_source.parameters.couchbase_port
        couchbase_host = virtual_source.connection.environment.host.name
        snapshot_id = str(helper_lib.get_snapshot_id())
        snapshot = SnapshotDefinition(db_path=db_path, couchbase_port=couchbase_port, couchbase_host=couchbase_host,
                                      bucket_list=bucket_list, time_stamp=time_stamp, snapshot_id=snapshot_id)
        logger.info("snapshot schema: {}".format(snapshot))
        return snapshot
    except Exception as error:
        handle_error_response(error, "Snap shot is failed ")


# This function returns the bucket name from snapshot.
def _find_bucket_name_from_snapshot(snapshot):
    bucket_list_and_size = snapshot.bucket_list
    logger.debug("SnapShot bucket data is: {}".format(bucket_list_and_size))
    # bucket_list_and_size contains the ramsize e.g. "Bucket1,122:Bucket2,3432"
    # Filtering the size from above information.
    bucket_list_and_size += ':'
    # Parsing logic because there could be bucket name having some digit
    # bucket details in snapshot : Bucket_name1,RamSize1:Bucket_name2,RamSize2:
    bucket_name = re.sub(',[0-9]*:', ':', bucket_list_and_size)
    bucket_name = bucket_name.strip(':')
    return bucket_name

def _find_bucket_size_byname(bucket_name, bucket_metadata):
    data_found = 0
    for bkt in bucket_metadata.split(':'):
        if bkt.split(',')[0] == bucket_name:
            logger.debug("Bucket {} found in list".format(bucket_name))
            data_found = 1
            bkt_size_mb = int(bkt.split(',')[1].strip()) // 1024 // 1024
            #logger.debug("bkt_size_mb = {}".format(bkt_size_mb))
            return bkt_size_mb
            break
    if data_found == 0:
        #raise exception. Ideally this condition should never occur
        pass