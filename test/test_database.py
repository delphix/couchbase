#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################

import pytest
from dlpx.virtualization.platform import Status

from src.utils import utilities
import test.constants as CS
from src.db_commands.commands import CommandFactory


def printlog(casenumber):
    if casenumber == 1:
        print "1. Command validated successfully"
    elif casenumber == 2:
        print "2. Positive test case validated"
    elif casenumber == 3:
        print "3. Negative test case validated"



def test_start_couchbase(main_class, monkeypatch, mock_run_bash):
    # positive test case
    kwargs = {'cmd': 'start_couchbase_cmd', 'test_type': CS.PASS}
    assert CommandFactory.start_couchbase(CS.INSTALL_PATH) == CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    def get_status():
        return Status.ACTIVE
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    monkeypatch.setattr(main_class, 'status', get_status)

    assert main_class.start_couchbase() is None
    printlog(2)
    #Negative test case
    kwargs['test_type'] = CS.FAIL
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    with pytest.raises(Exception) as err:
        main_class.start_couchbase()
    err.match(r'.*Internal error occurred*')
    printlog(3)


def test_bucket_create(main_class, monkeypatch, mock_run_bash):
    # positive test case

    kwargs = {'cmd': 'bucket_create_cmd', 'test_type': CS.PASS}
    assert CommandFactory.bucket_create(CS.shell_path, CS.hostname, CS.port, CS.username, CS.bucket_name, CS.ramsize,
                                        CS.evictionpolicy) == \
           CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.bucket_create(CS.bucket_name, CS.ramsize) is None
    printlog(2)
    # Negative test case
    kwargs['test_type'] = CS.FAIL
    kwargs['data_index'] = 0
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    with pytest.raises(Exception) as err:
        main_class.bucket_create(CS.bucket_name, CS.ramsize)
    err.match(r'.*Provided bucket size is not suffice to proceed*')
    printlog(3)


def test_bucket_delete(main_class, monkeypatch, mock_run_bash):
    # positive test case
    kwargs = {'cmd': 'bucket_delete_cmd', 'test_type': CS.PASS}
    assert CommandFactory.bucket_delete(CS.shell_path, CS.hostname, CS.port, CS.username, CS.bucket_name) == \
           CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.bucket_delete(CS.bucket_name)[2] == 0
    printlog(2)
    # Negative test case
    kwargs['test_type'] = CS.FAIL
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    with pytest.raises(Exception) as err:
        main_class.bucket_delete(CS.bucket_name)
    err.match(r'.*Internal error occurred*')
    printlog(3)


def test_node_init_cmd(main_class, monkeypatch, mock_run_bash):
    # positive test case
    kwargs = {'cmd': 'node_init_cmd', 'test_type': CS.PASS}
    assert CommandFactory.node_init(CS.shell_path, CS.port, CS.username, CS.mount_path) == \
           CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.node_init() is None
    printlog(2)
    # Negative test case
    kwargs['test_type'] = CS.FAIL
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    main_class.node_init()
    printlog(3)


def test_cluster_init_cmd(main_class, monkeypatch, mock_run_bash):
    # positive test case
    kwargs = {'cmd': 'cluster_init_cmd', 'test_type': CS.PASS}
    assert CommandFactory.cluster_init(CS.shell_path, CS.hostname, CS.port, CS.username, CS.ramsize, CS.cluster_name,
                                       CS.cluster_index_ramsize, CS.cluster_fts_ramsize, CS.cluster_eventing_ramsize,
                                       CS.cluster_analytics_ramsize, CS.additional_services) == \
           CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.cluster_init()[2] == 0
    printlog(2)
    # Negative test case
    kwargs['test_type'] = CS.FAIL
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.cluster_init()[2] == 1
    printlog(3)


def test_xdcr_replicate_cmd(main_class, monkeypatch, mock_run_bash):
    # positive test case
    kwargs = {'cmd': 'xdcr_replicate_cmd', 'test_type': CS.PASS}
    assert CommandFactory.xdcr_replicate(CS.shell_path, CS.source_hostname, CS.source_port, CS.source_username,CS.source_bucket_name, CS.target_bucket_name, CS.cluster_name, CS.hostname, CS.port, CS.username) == CS.CMD_TEST_DATA[kwargs['cmd']][0]
    printlog(1)
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.xdcr_replicate(CS.bucket_name, CS.bucket_name) is None
    printlog(2)
    # Negative test case
    kwargs['test_type'] = CS.FAIL
    monkeypatch.setattr('test.test_database.utilities.libs.run_bash', mock_run_bash(None, None, **kwargs))
    assert main_class.xdcr_replicate(CS.bucket_name, CS.bucket_name) is None
    printlog(3)
