#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
# In this module, VDB related operations are implemented.
"""
#######################################################################################################################

import re
import json

# Auto generated libs
import sys

from generated.definitions import SnapshotDefinition
from generated.definitions import SourceConfigDefinition

from internal_exceptions.database_exceptions import FailedToReadBucketDataFromSnapshot, CouchbaseServicesError
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
import logging
from controller.resource_builder import Resource

# Global logger for this File
logger = logging.getLogger(__name__)


def vdb_status(virtual_source, repository, source_config):
    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
            source_config).build())
    cb_status = provision_process.status()
    logger.debug("VDB Status is {}".format(cb_status))
    return cb_status


def vdb_unconfigure(virtual_source, repository, source_config):
    # delete all buckets
    provision_process = CouchbaseOperation(
    Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
        source_config).build())

    vdb_stop(virtual_source, repository, source_config)
    provision_process.delete_config()



def vdb_reconfigure(virtual_source, repository, source_config, snapshot):
    # delete all buckets
    # calll configure

    logger.debug("In vdb_reconfigure...")
    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
            source_config).build())

    provision_process.restore_config(what='current')

    vdb_start(virtual_source, repository, source_config)
    return _source_config(virtual_source, repository, source_config, snapshot)


def vdb_configure(virtual_source, snapshot, repository):
    # try:

    logger.debug("VDB CONFIG START")
    logger.debug(snapshot)

    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_snapshot(
            snapshot).build())





    # TODO:
    # fail if already has cluster ?

    # to make sure there is no config 
    provision_process.delete_config()


    provision_process.restore_config(what='parent')

    # if bucket doesn't existing in target cluster 
    # couchbase will delete directory while starting 
    # so we have to rename it before start

    bucket_list_and_size = json.loads(snapshot.bucket_list)

    if not bucket_list_and_size:
        raise FailedToReadBucketDataFromSnapshot("Snapshot Data is empty.")
    else:
        logger.debug("snapshot bucket data is: {}".format(bucket_list_and_size))



    # for item in helper_lib.filter_bucket_name_from_output(bucket_list_and_size):
    #     logger.debug("Checking bucket: {}".format(item))
    #     bucket_name = item.split(',')[0]
    #     # rename folder
    #     provision_process.move_bucket(bucket_name, 'save')

    provision_process.restart_couchbase(provision=True)
    provision_process.rename_cluster()
    #provision_process.node_init()
    #provision_process.cluster_init()
    
    
    #_do_provision(provision_process, snapshot)
    #_cleanup(provision_process, snapshot)

    #_build_indexes(provision_process, snapshot)

    src_cfg_obj = _source_config(virtual_source, repository, None, snapshot)

    return src_cfg_obj
    # except FailedToReadBucketDataFromSnapshot as err:
    #     raise FailedToReadBucketDataFromSnapshot("Provision is failed. " + err.message).to_user_error(), None, \
    #         sys.exc_info()[2]
    # except Exception as err:
    #     logger.debug("Provision is failed {}".format(err.message))
    #     raise



def _do_provision(provision_process, snapshot):
    bucket_list_and_size = snapshot.bucket_list

    if not bucket_list_and_size:
        raise FailedToReadBucketDataFromSnapshot("Snapshot Data is empty.")
    else:
        logger.debug("snapshot bucket data is: {}".format(bucket_list_and_size))

    bucket_list_and_size = json.loads(bucket_list_and_size)

    try:
        bucket_list = provision_process.bucket_list()
        bucket_list = helper_lib.filter_bucket_name_from_output(bucket_list)
        logger.debug(bucket_list)
    except Exception as err:
        logger.debug("Failed to get bucket list. Error is " + err.message)


    renamed_folders = []

    for item in bucket_list_and_size:
        logger.debug("Checking bucket: {}".format(item))
        # try:
        bucket_name = item['name']
        bkt_size = item['ram']
        bkt_type = item['bucketType']
        bkt_compression = item['compressionMode']
        bkt_size_mb = helper_lib.get_bucket_size_in_MB(0, bkt_size)
        if bucket_name not in bucket_list:
            # a new bucket needs to be created
            logger.debug("Creating bucket: {}".format(bucket_name))
            provision_process.bucket_create(bucket_name, bkt_size_mb, bkt_type, bkt_compression)
            helper_lib.sleepForSecond(2)
        else:
            logger.debug("Bucket {} exist - no need to rename directory".format(bucket_name))

    
    provision_process.stop_couchbase()

    for item in helper_lib.filter_bucket_name_from_output(bucket_list_and_size):
        logger.debug("Checking bucket: {}".format(item))
        bucket_name = item.split(',')[0]
        logger.debug("restoring folders")
        provision_process.move_bucket(bucket_name, 'restore')
    
    
    provision_process.start_couchbase()

    # getting config directory path
    directory = provision_process.get_config_directory()

    # making directory and changing permission to 755.
    provision_process.make_directory(directory)
    # This file path is being used to store the bucket information coming in snapshot
    config_file_path = provision_process.get_config_file_path()

    #content = "BUCKET_LIST=" + _find_bucket_name_from_snapshot(snapshot)

    # Adding bucket list in config file path .config file, inside .delphix folder
    #helper_lib.write_file(provision_process.connection, content, config_file_path)


def _cleanup(provision_process, snapshot):
    logger.debug("Deleting extra buckets from target host")
    bucket_list = []
    # Get details of already exist buckets on the target server. We need to delete if some of these are not needed
    try:
        bucket_list = provision_process.bucket_list()
        logger.debug(bucket_list)
        # Removing extra information captured like ramsize, ramused. Only need to get bucket name from output
        bucket_list = helper_lib.filter_bucket_name_from_output(bucket_list)
    except Exception as err:
        logger.debug("Failed to get bucket list. Error is " + err.message)

    snapshot_bucket_list_and_size = snapshot.bucket_list
    snapshot_bucket = _find_bucket_name_from_snapshot(snapshot)

    if (snapshot_bucket):
        logger.debug("BUCKET_LIST to be provisioned: {}".format(snapshot_bucket))
        snapshot_bucket_list = snapshot_bucket.split(':')
        bucket_to_delete = []
        bucket_to_update = []
        for bkt in bucket_list:
            if bkt not in snapshot_bucket_list:
                bucket_to_delete.append(bkt)
            else:
                bucket_to_update.append(bkt)

        logger.debug("Bucket list to delete: {} ".format(bucket_to_delete))
        _bucket_common_task(provision_process, bucket_to_delete)
        logger.debug("Bucket list to update: {} ".format(bucket_to_update))
        _bucket_modify_task(provision_process, bucket_to_update, snapshot_bucket_list_and_size)
    else:
        logger.debug("This block is not expected to run")


def _bucket_common_task(provision_process, bucket_list):
    for bkt in bucket_list:
        bkt = bkt.strip()
        logger.debug("Deletion of bucket {} started".format(bkt))
        provision_process.bucket_edit(bkt, flush_value=1)
        provision_process.bucket_flush(bkt)
        provision_process.bucket_edit(bkt, flush_value=0)
        provision_process.bucket_delete(bkt)
        helper_lib.sleepForSecond(2)


def _bucket_modify_task(provision_process, bucket_list, snapshot_bucket_list_and_size):
    for bkt in bucket_list:
        bkt = bkt.strip()
        logger.debug("Modification of bucket {} started".format(bkt))
        ramquotasize = _find_bucket_size_byname(bkt, snapshot_bucket_list_and_size)
        logger.debug("Update bucket {} with ramsize {}MB".format(bkt, ramquotasize))
        provision_process.bucket_edit_ramquota(bkt, _ramsize=ramquotasize)
        helper_lib.sleepForSecond(2)


def _source_config(virtual_source, repository=None, source_config=None, snapshot=None):
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


def vdb_start(virtual_source, repository, source_config):
    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
            source_config).build())
    logger.debug("Starting couchbase server")
    try:
        provision_process.start_couchbase()
    except Exception:
        raise CouchbaseServicesError(" Start").to_user_error(), None, sys.exc_info()[2]


def vdb_stop(virtual_source, repository, source_config):
    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
            source_config).build())
    logger.debug("Stopping couchbase server")
    provision_process.stop_couchbase()


def vdb_pre_snapshot(virtual_source, repository, source_config):
    logger.debug("In Pre snapshot...")
    provision_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
            source_config).build())

    provision_process.save_config(what='parent')
    provision_process.save_config(what='current')


def post_snapshot(virtual_source, repository, source_config):
    try:
        logger.debug("Taking Post Snapshot...")
        provision_process = CouchbaseOperation(
            Resource.ObjectBuilder.set_virtual_source(virtual_source).set_repository(repository).set_source_config(
                source_config).build())
        # config_file = provision_process.get_config_file_path()

        # stdout, stderr, exit_code = helper_lib.read_file(virtual_source.connection, config_file)
        # bucket_list = re.sub('BUCKET_LIST=', '', stdout)

        ind = provision_process.get_indexes_definition()
        logger.debug("indexes definition : {}".format(ind))

        bucket_details = json.dumps(provision_process.bucket_list())
        logger.debug("BUCKET_LIST={}".format(bucket_details))
        db_path = virtual_source.parameters.mount_path
        time_stamp = helper_lib.current_time()
        couchbase_port = virtual_source.parameters.couchbase_port
        couchbase_host = virtual_source.connection.environment.host.name
        snapshot_id = str(helper_lib.get_snapshot_id())
        snapshot = SnapshotDefinition(db_path=db_path, couchbase_port=couchbase_port, couchbase_host=couchbase_host,
                                      bucket_list=bucket_details, time_stamp=time_stamp, snapshot_id=snapshot_id, indexes = ind)

        snapshot.couchbase_admin = provision_process.parameters.couchbase_admin
        snapshot.couchbase_admin_password = provision_process.parameters.couchbase_admin_password
                              
        logger.info("snapshot schema: {}".format(snapshot))
        return snapshot
    except Exception as err:
        logger.debug("Snap shot is failed with error {}".format(err.message))
        raise


# This function returns the bucket name from snapshot.
def _find_bucket_name_from_snapshot(snapshot):
    bucket_list_and_size = json.loads(snapshot.bucket_list)
    logger.debug("SnapShot bucket data is: {}".format(bucket_list_and_size))
    # # bucket_list_and_size contains the ramsize e.g. "Bucket1,122:Bucket2,3432"
    # # Filtering the size from above information.
    # bucket_list_and_size += ':'
    # # Parsing logic because there could be bucket name having some digit
    # # bucket details in snapshot : Bucket_name1,RamSize1:Bucket_name2,RamSize2:
    # bucket_name = re.sub(',[0-9]*:', ':', bucket_list_and_size)
    # bucket_name = bucket_name.strip(':')
    bucket_name = helper_lib.filter_bucket_name_from_output(bucket_list_and_size)
    return bucket_name


def _find_bucket_size_byname(bucket_name, bucket_metadata):
    data_found = 0
    for bkt in bucket_metadata.split(':'):
        if bkt.split(',')[0] == bucket_name:
            logger.debug("Bucket {} found in list".format(bucket_name))
            data_found = 1
            bkt_size_mb = int(bkt.split(',')[1].strip()) // 1024 // 1024
            return bkt_size_mb
    if data_found == 0:
        # raise exception. Ideally this condition should never occur
        raise Exception("Failed to find the bucket_name from bucket_metadata list")


def _build_indexes(provision_process, snapshot):
    logger.debug("index builder")

    for i in snapshot.indexes:
        logger.debug(i)
        provision_process.build_index(i)