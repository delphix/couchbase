#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################

import pytest
from src.utils import utilities
import test.constants as CS
from src.db_commands.commands import CommandFactory
from src.controller.helper_lib import get_snapshot_id,get_all_bucket_list_with_size, get_bucket_name_with_size,\
    get_bucket_size_in_MB



def test_couchbase_factory(get_couchbase_object,virtual_source , staged_source, repository,
                           snapshot_parameters,source_connection, source_config, snapshot):
    print ("creating object for the case: repository_discovery")

    kwargs = {'connection': source_connection}
    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: source_config_discovery")
    kwargs = {'connection': source_connection, 'repository': repository}
    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: D_source Snapshot")
    snapshot_parameters.resync=False
    kwargs = {'source_config': source_config, 'repository': repository, 'staged_source': staged_source,
              'snapshot_parameters': snapshot_parameters }

    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: D_source status, D_source disable, D_source enable")
    kwargs = {'source_config': source_config, 'repository': repository, 'staged_source': staged_source }
    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: vdb configure")
    kwargs = {'repository': repository, 'snapshot': snapshot, 'virtual_source': virtual_source}
    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: vdb reconfigure")
    kwargs = {'repository': repository, 'snapshot': snapshot, 'virtual_source': virtual_source, 'source_config': source_config}
    obj = get_couchbase_object(**kwargs)

    print("creating object for the case: vdb pre_snapshot")
    kwargs = {'repository': repository, 'source_config': source_config, 'virtual_source': virtual_source}
    obj = get_couchbase_object(**kwargs)

    kwargs = {'repository': repository, 'source_config': source_config, 'dummy': virtual_source}

    with pytest.raises(Exception) as err:
        obj = get_couchbase_object(**kwargs)
    err.match(r'.*Invalid key passed*')


def test_snapshot_id_generation():
    print "Test snapshot id generator."
    counter = 1
    total_snap_ids = []
    id = get_snapshot_id()
    while counter <= 200 and id not in total_snap_ids:
        print " Checking id : {}".format(id)
        total_snap_ids.append(id)
        id = get_snapshot_id()
        counter = counter + 1
    assert counter == 201

def test_get_all_bucket_list_with_size():
    print "Validating the function get_all_bucket_list_with_size"
    bucket_output="""beer-sample
 bucketType: membase
 numReplicas: 1
 ramQuota: 104857600
 ramUsed: 17992995844
gamesim-sample
 bucketType: membase
 numReplicas: 1
 ramQuota: 94857600
 ramUsed: 14847224
travel-sample
 bucketType: membase
 numReplicas: 1
 ramQuota: 114857600
 ramUsed: 104857600"""
    output = get_all_bucket_list_with_size(bucket_output.split("\n"))

    for each_bucket in output:
        bkt, ramUsed = each_bucket.split(",")
        print bkt, ramUsed
        if bkt == "beer-sample":
            if ramUsed == "9896147714":
                print " beer-sample data is correct"
            else:
                raise Exception("Invalid bucket size got for beer-sample")
        elif bkt == "gamesim-sample":
            if ramUsed == "104857600":
                print " gamesim-sample data is correct"
            else:
                raise Exception("Invalid bucket size got for gamesim-sample")
        elif bkt == "travel-sample":
            if ramUsed == "104857600":
                print " travel-sample data is correct"
            else:
                raise Exception("Invalid bucket size got for travel-sample")
        elif bkt != " ":
            raise Exception("Invalid bucket name identified")


def test_get_bucket_name_with_size():
    print "Finding specific bucket with size from bucket output"
    bucket_output = """
    beer-sample
     bucketType: membase
     numReplicas: 1
     ramQuota: 104857600
     ramUsed: 17992995844
    gamesim-sample
     bucketType: membase
     numReplicas: 1
     ramQuota: 94857600
     ramUsed: 14847224
    travel-sample
     bucketType: membase
     numReplicas: 1
     ramQuota: 114857600
     ramUsed: 104857600
     """
    output = get_bucket_name_with_size(bucket_output.split("\n"), "beer-sample")
    print output
    if output.split(',')[1] == "9896147714":
        print " Verified for beer-sample"
    output = get_bucket_name_with_size(bucket_output.split("\n"), "gamesim-sample")
    if output.split(',')[1] == "104857600":
        print " Verified for gamesim-sample"
    output = get_bucket_name_with_size(bucket_output.split("\n"), "travel-sample")
    if output.split(',')[1] == "104857600":
        print " Verified for travel-sample"
    #TODO
    #Add test case for bucket which is not present
    #Add test case for bucket name with special chars


def test_get_bucket_size_in_MB():
    print ("Testing conversion of bucket size into MegaByte")
    case=""
    output = get_bucket_size_in_MB(0, 10000000)
    print output
    if output!=9:
        case+="1, "
    output = get_bucket_size_in_MB(1, 1)
    if output!=1:
        case += "2, "
    print output
    output = get_bucket_size_in_MB(0, 1)
    if output != 0:
        case += "3, "
    print output
    output = get_bucket_size_in_MB(0, 0)
    if output != 0:
        case += "4, "
    print output
    output = get_bucket_size_in_MB(100000, 1)
    if output != 100000:
        case += "5, "
    print output
    if case!="":
        pytest.fail(" Failed for the case : {}".format(case))





















