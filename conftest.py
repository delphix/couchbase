#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################

import pytest
from dlpx.virtualization.common._common_classes import RemoteUser, RemoteHost, RemoteEnvironment, RemoteConnection
from dlpx.virtualization.platform import StagedSource, Mount, VirtualSource

import sys

sys.path.append('src')
from src.controller.couchbase_operation import CouchbaseOperation
from src.controller.resource_builder import Resource
from src.generated.definitions.linked_source_definition import LinkedSourceDefinition
from src.generated.definitions.repository_definition import RepositoryDefinition
from src.generated.definitions.source_config_definition import SourceConfigDefinition
from src.generated.definitions.snapshot_parameters_definition import SnapshotParametersDefinition
from src.generated.definitions.virtual_source_definition import VirtualSourceDefinition
from src.generated.definitions.snapshot_definition import SnapshotDefinition

from test import constants


############# Fixtures for connection related classes defined in vsdk #################################################
@pytest.fixture(scope="session", autouse=True)
def user():
    return RemoteUser(constants.username, constants.UserReference)


@pytest.fixture(scope="session", autouse=True)
def host():
    return RemoteHost(constants.hostname, constants.HostReference, constants.BINARY_PATH, constants.ScratchPath)


@pytest.fixture(scope="session", autouse=True)
def environment(host):
    return RemoteEnvironment(constants.Environment, constants.EnvironmentReference, host)


@pytest.fixture(scope="session", autouse=True)
def source_connection(environment, user):
    return RemoteConnection(environment, user)


#######################################################################################################################


############# Fixtures for objects received in plugin_runner.py #######################################################

@pytest.fixture(scope="session", autouse=True)
def staged_connection(source_connection):
    return source_connection


@pytest.fixture(scope="session", autouse=True)
def source_config():
    return SourceConfigDefinition(couchbase_src_port=constants.source_port,
                                  couchbase_src_host=constants.source_hostname,
                                  pretty_name=constants.pretty_name,
                                  db_path=constants.db_path)


@pytest.fixture(scope="session", autouse=True)
def snapshot_parameters():
    return SnapshotParametersDefinition(resync=True)


@pytest.fixture(scope="session", autouse=True)
def virtual_source_parameters():
    return VirtualSourceDefinition(cluster_ftsram_size=constants.cluster_fts_ramsize,
                                   eventing_service=True,
                                   cluster_index_ram_size=constants.cluster_index_ramsize,
                                   cluster_eventing_ram_size=constants.cluster_eventing_ramsize,
                                   couchbase_port=constants.port,
                                   tgt_cluster_name=constants.target_cluster_name,
                                   cluster_ram_size=constants.cluster_ramsize,
                                   mount_path=constants.mount_path,
                                   fts_service=True,
                                   bucket_eviction_policy=constants.evictionpolicy,
                                   couchbase_admin='Administrator',
                                   analytics_service=True,
                                   cluster_analytics_ram_size=constants.cluster_analytics_ramsize,
                                   couchbase_admin_password='')


@pytest.fixture(scope="session", autouse=True)
def snapshot():
    return SnapshotDefinition(db_path=constants.db_path,
                              couchbase_port=constants.port,
                              couchbase_host=constants.hostname,
                              bucket_list=constants.bucket_name,
                              time_stamp=constants.timestamp,
                              snapshot_id=constants.snapshot_id)


@pytest.fixture(scope="session", autouse=True)
def staged_parameters_xdcr():
    return LinkedSourceDefinition(
        cluster_ftsram_size=constants.cluster_fts_ramsize,
        couchbase_port=constants.port,
        xdcr_admin='Administrator',
        cluster_index_ram_size=constants.cluster_index_ramsize,
        bucket_eviction_policy='valueOnly',
        eventing_service=True, couchbase_bak_repo='',
        couchbase_bak_loc='', config_settings_prov=None,
        stg_cluster_name='', couchbase_host='',
        couchbase_admin_password='', fts_service=True,
        couchbase_admin='Administrator', mount_path='',
        xdcr_admin_password='',
        cluster_eventing_ram_size=constants.cluster_eventing_ramsize,
        cluster_ram_size=constants.ramsize,
        d_source_type='XDCR', analytics_service=True,
        cluster_analytics_ram_size=constants.cluster_analytics_ramsize,
        bucket_size=0,
        validate=True)


@pytest.fixture(scope="session", autouse=True)
def repository():
    return RepositoryDefinition(cb_shell_path=constants.shell_path,
                                version=constants.version,
                                cb_install_path=constants.INSTALL_PATH,
                                pretty_name=constants.pretty_name,
                                validate=True)


@pytest.fixture(scope="session", autouse=True)
def mount(environment):
    return Mount(environment, constants.mount_path, None)


@pytest.fixture(scope="session", autouse=True)
def staged_source(source_connection, staged_connection, staged_parameters_xdcr, mount):
    staged_source = StagedSource(constants.UID, source_connection, staged_parameters_xdcr, mount, staged_connection)
    return staged_source


@pytest.fixture(scope="session", autouse=True)
def virtual_source(source_connection, staged_connection, virtual_source_parameters, mount):
    staged_source = VirtualSource(constants.GID, source_connection, virtual_source_parameters, mount)
    return staged_source


########################################################################################################################


############# Fixture to create object of main class: CouchbaseOperation #########################################
@pytest.fixture(scope="session", autouse=True)
def main_class(staged_source, repository):
    obj = CouchbaseOperation(Resource.ObjectBuilder.set_staged_source(staged_source)
                             .set_repository(repository).set_dsource(True).build())
    return obj


@pytest.fixture(scope="session", autouse=True)
def get_couchbase_object():
    def couchbase_object_factory(**kwargs):
        params = kwargs.keys()
        obj_builder = Resource.ObjectBuilder
        for key in params:
            if key == "staged_source":
                print " Setting staged_source"
                obj_builder.set_staged_source(kwargs[key])
            elif key == "dsource":
                print " Setting dsource"
                obj_builder.set_dsource(kwargs[key])
            elif key == "virtual_source":
                print " Setting staged_source"
                obj_builder.set_virtual_source(kwargs[key])
            elif key == "repository":
                print " Setting repository"
                obj_builder.set_repository(kwargs[key])
            elif key == "source_config":
                print " Setting source_config"
                obj_builder.set_source_config(kwargs[key])
            elif key == "connection":
                print " Setting connection"
                obj_builder.set_connection(kwargs[key])
            elif key == "snapshot_parameters":
                print " Setting snapshot_parameters"
                obj_builder.set_snapshot_parameters(kwargs[key])
            elif key == "snapshot":
                print " Setting snapshot"
                obj_builder.set_snapshot(kwargs[key])
            else:
                raise Exception("Invalid key passed")
        obj_builder.build()
        cb_obj = CouchbaseOperation(obj_builder)
        return cb_obj

    return couchbase_object_factory


#######################################################################################################################


############# Fixture to mock the output of each command which is executing through run_bash #############
class MockBashResponse(object):
    def __init__(self, command_output, error_string, code):
        self._stdout = command_output
        self._stderr = error_string
        self._exit_code = code

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    @property
    def exit_code(self):
        return self._exit_code

    def __call__(self, *args, **kwargs):
        return self


@pytest.fixture(scope="session", autouse=True)
def mock_run_bash():
    def mock_run_bash_inner(connection=None, command=None, **kwargs):

        cmd = kwargs['cmd']
        result_type = kwargs['test_type'] if 'test_type' in kwargs.keys() else constants.PASS
        INDEX = kwargs['data_index'] if 'data_index' in kwargs.keys() else 0
        if cmd is not None and result_type is not None:
            data = constants.CMD_TEST_DATA[cmd][result_type]
            return MockBashResponse(data[INDEX][constants.OUTPUT], data[INDEX][constants.ERROR],
                                    data[INDEX][constants.EXIT])
        if cmd is None:
            raise Exception("cmd cannot be None")
        if cmd not in constants.CMD_TEST_DATA.keys():
            raise Exception("Invalid command {} passed".format(cmd))

    return mock_run_bash_inner
########################################################################################################################
