#
# Copyright (c) 2020 by Delphix. All rights reserved.
#
#######################################################################################################################

INSTALL_PATH = "/opt/couchbase/couchbase-server"
BINARY_PATH = "/opt/couchbase/bin"
shell_path = "/opt/couchbase/couchbase-cli"
hostname = "hostname"
port = 8091
username = "user"
cluster_name = "cluster"
cluster_ramsize = 100
cluster_index_ramsize = 200
cluster_fts_ramsize = 300
cluster_eventing_ramsize = 400
cluster_analytics_ramsize = 500
additional_services = "query,index,data"
source_hostname = "source_hostname"
source_port = 8091
source_username = "source_username"
source_bucket_name = "source_bucket_name"
target_bucket_name = "target_bucket_name"
uuid = "123456789"
directory_path = "/mnt/provision/test/directory_path"
mount_path = "/mnt/provision/mount_path"
bucket_name = "sample"
flush_value = "0"
ramsize = 100
evictionpolicy = "valueOnly"
base_path = "base_path"
index = "index"
index_name = "index_name"
backup_location = "backup_location"
backup_repo = "backup_repo"
csv_bucket_list = "csv_bucket_list"
filename = "filename"
file_path = "test"
data = "data"
dir_path = "/tmp/.delphix"
DLPX_BIN_JQ = "/tmp"
version = "1.1"
pretty_name = "couchbase"
db_path = "/var/data/lib"
target_cluster_name = "target_cluster_name"
couchbase_admin_password="password"
timestamp=""
snapshot_id="12345"

# Delphix Related
UserReference = "user-reference"
HostReference = "host-reference"
ScratchPath = "scratch_path"
Environment = "environment"
EnvironmentReference = "environment-reference"
UID = 1
GID = 2

# unit test related
PASS = 1
FAIL = 2
OUTPUT = 0
ERROR = 1
EXIT = 2

CMD_TEST_DATA = {'start_couchbase_cmd':
                     [INSTALL_PATH + ' \-- -noinput -detached .',
                      [("", "", 0)],
                      [("command not found", "", 1)]],
                 'bucket_create_cmd':
                     ['/opt/couchbase/couchbase-cli bucket-create --cluster 127.0.0.1:8091 --username user --password $password --bucket sample --bucket-type couchbase --bucket-ramsize 100 --bucket-replica 0 --bucket-eviction-policy valueOnly --compression-mode passive --conflict-resolution sequence --wait',
                      [("SUCCESS: Bucket created", "", 0)],
                      [("ramQuotaMB - RAM quota cannot be less than 100 MB", "", 1)]],
                 'bucket_delete_cmd':
                     ['/opt/couchbase/couchbase-cli bucket-delete --cluster hostname:8091 --username user --password $password  --bucket=sample',
                      [("SUCCESS: Bucket deleted", "", 0)],
                      [("Bucket not found", "", 1)]],
                 'node_init_cmd':
                     ['/opt/couchbase/couchbase-cli node-init  --cluster 127.0.0.1:8091 --username user --password $password --node-init-data-path /mnt/provision/mount_path/data  --node-init-index-path /mnt/provision/mount_path/data --node-init-analytics-path /mnt/provision/mount_path/data  --node-init-hostname 127.0.0.1',
                      [("SUCCESS: Node initialized", "", 0)],
                      [("Changing data of nodes that are part of provisioned cluster is not supported", "", 1)]],
                 'cluster_init_cmd':
                     ['/opt/couchbase/couchbase-cli cluster-init --cluster hostname:8091 --cluster-username user --cluster-password $password --cluster-ramsize 100 --cluster-name cluster --cluster-index-ramsize 200  --cluster-fts-ramsize 300  --cluster-eventing-ramsize 400 --cluster-analytics-ramsize 500 --services data,index,query,index,data',
                      [("SUCCESS: Cluster initialized", "", 0)],
                      [("ERROR: Cluster is already initialized, use setting-cluster to change settings", "", 1)]],
                 'xdcr_replicate_cmd':
                     ['/opt/couchbase/couchbase-cli xdcr-replicate --cluster source_hostname:8091 --username source_username --password $source_password --create --xdcr-from-bucket source_bucket_name --xdcr-to-bucket target_bucket_name --xdcr-cluster-name cluster',
                      [("XDCR replication create succeeded", "", 0)],
                      [("Already XDCR set up have been between source and staging server", "", 1)]],
                 }
