#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
CommandFactory class contains all commands required to perform couchbase and OS related operations
These are a list of commands which are being used in this project. Have segregated both types of commands into two
classes DatabaseCommand and OSCommand. CommandFactory is the actual class through which the command string will be
returned. In the last section of this file, we have created small tests for all these commands with dummy values.
Through which we can see the actual command is going to execute. All methods are decorated to @staticmethod,
so no need to create an object of the class, we can use the direct class name to use any command method
"""
#######################################################################################################################


class OSCommand(object):
    def __init__(self):
        pass

    @staticmethod
    def find_binary_path():
        return "echo $COUCHBASE_PATH"

    @staticmethod
    def find_install_path(binary_path):
        return "find {binary_path} -name couchbase-server".format(binary_path=binary_path)

    @staticmethod
    def find_shell_path(binary_path):
        return "find {binary_path} -name couchbase-cli".format(binary_path=binary_path)

    @staticmethod
    def get_process():
        return "ps -ef"

    @staticmethod
    def make_directory(directory_path,sudo=False, uid=None):
        if sudo:
            return "sudo -u \#{uid} mkdir -p {directory_path}".format(uid=uid, directory_path=directory_path)
        else:
            return "mkdir -p {directory_path}".format(directory_path=directory_path)

    @staticmethod
    def change_permission(path,sudo=False, uid=None):
        if sudo:
            return "sudo -u \#{uid} chmod -R 775 {path}".format(uid=uid, path=path)
        else:
            return "chmod -R 775 {path}".format(path=path)

    @staticmethod
    def get_config_directory(mount_path):
        return "{mount_path}/.delphix".format(mount_path=mount_path)

    @staticmethod
    def read_file(filename):
        return "cat {filename}".format(filename=filename)

    @staticmethod
    def check_file(file_path):
        return "[ -f {file_path} ] && echo 'Found'".format(file_path=file_path)

    @staticmethod
    def write_file(filename, data):
        return "echo {data} > {filename}".format(filename=filename, data=data)

    @staticmethod
    def get_ip_of_hostname():
        return "hostname -i"

    @staticmethod
    def check_directory(dir_path):
        return "[ -d {dir_path} ] && echo 'Found'".format(dir_path=dir_path)

    @staticmethod
    def delete_file(filename):
        return "rm  -f  {filename}".format(filename=filename)

    @staticmethod
    def delete_dir(dirname):
        return "rm  -rf  {dirname}".format(dirname=dirname)

    @staticmethod
    def os_mv(srcname, trgname):
        return "mv {srcname} {trgname}".format(srcname=srcname, trgname=trgname)

    @staticmethod
    def get_dlpx_bin():
        return "echo $DLPX_BIN_JQ"

    @staticmethod
    def unmount_file_system(mount_path):
        return "sudo /bin/umount {mount_path}".format(mount_path=mount_path)

    @staticmethod
    def whoami():
        # uid=1003(delphix) gid=1003(delphix) groups=1003(delphix) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
        return "id"


    @staticmethod
    def sed(filename, regex):
        return 'sed -i -e "{}" {}'.format(regex, filename)

class DatabaseCommand(object):
    def __init__(self):
        pass

    @staticmethod
    def start_couchbase(install_path, sudo=False, uid=None):
        if sudo:
            return "sudo -u \#{} {install_path} \-- -noinput -detached .".format(uid, install_path=install_path)
        else:
            return "{install_path} \-- -noinput -detached .".format(install_path=install_path)

    @staticmethod
    def get_version(install_path):
        return "{install_path} --version".format(install_path=install_path)

    @staticmethod
    def get_ids(install_path):
        #-rwxr-xr-x. 1 996 993 514 Jan 30  2020 /opt/couchbase/bin/couchbase-cli
        return "ls -n {install_path}".format(install_path=install_path)


    @staticmethod
    def get_data_directory(couchbase_base_dir):
        return "cat {couchbase_base_dir}/etc/couchbase/static_config|grep path_config_datadir".format(
            couchbase_base_dir=couchbase_base_dir)

    @staticmethod
    def stop_couchbase(install_path, sudo=False, uid=None):
        if sudo:
            return "sudo -u \#{} {install_path} -k".format(uid, install_path=install_path)
        else:
            return "{install_path} -k".format(install_path=install_path)

    @staticmethod
    def cluster_init(shell_path,
                     hostname,
                     port,
                     username,
                     cluster_ramsize,
                     cluster_name,
                     cluster_index_ramsize,
                     cluster_fts_ramsize,
                     cluster_eventing_ramsize,
                     cluster_analytics_ramsize,
                     additional_services
                     ):
        return "{shell_path} cluster-init --cluster {hostname}:{port} --cluster-username {username} --cluster-password $password --cluster-ramsize {cluster_ramsize} --cluster-name {cluster_name} --cluster-index-ramsize {cluster_index_ramsize}  --cluster-fts-ramsize {cluster_fts_ramsize}  --cluster-eventing-ramsize {cluster_eventing_ramsize} --cluster-analytics-ramsize {cluster_analytics_ramsize} --services data,index,{additional_services}".format(
            shell_path=shell_path,
            hostname=hostname,
            username=username,
            port=port,
            cluster_ramsize=cluster_ramsize,
            cluster_name=cluster_name,
            cluster_index_ramsize=cluster_index_ramsize,
            cluster_fts_ramsize=cluster_fts_ramsize,
            cluster_eventing_ramsize=cluster_eventing_ramsize,
            cluster_analytics_ramsize=cluster_analytics_ramsize,
            additional_services=additional_services
        )

    @staticmethod
    def cluster_setting(shell_path, hostname, port, username, cluster_ramsize, cluster_name, cluster_index_ramsize,
                        cluster_fts_ramsize, cluster_eventing_ramsize, cluster_analytics_ramsize):
        return "{shell_path} setting-cluster -c {hostname}:{port} -u {username} -p $password --cluster-ramsize {cluster_ramsize} --cluster-name {cluster_name} --cluster-index-ramsize {cluster_index_ramsize} --cluster-fts-ramsize {cluster_fts_ramsize} --cluster-eventing-ramsize {cluster_eventing_ramsize} --cluster-analytics-ramsize {cluster_analytics_ramsize}".format(
            shell_path=shell_path,
            hostname=hostname,
            port=port,
            username=username,
            cluster_ramsize=cluster_ramsize,
            cluster_name=cluster_name,
            cluster_index_ramsize=cluster_index_ramsize,
            cluster_fts_ramsize=cluster_fts_ramsize,
            cluster_eventing_ramsize=cluster_eventing_ramsize,
            cluster_analytics_ramsize=cluster_analytics_ramsize
        )

    @staticmethod
    def xdcr_setup(shell_path, source_hostname, source_port, source_username, hostname, port, username, cluster_name):
        return "{shell_path} xdcr-setup --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --create --xdcr-hostname {hostname}:{port} --xdcr-username {username} --xdcr-password $password --xdcr-cluster-name {cluster_name}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            hostname=hostname,
            port=port,
            username=username,
            cluster_name=cluster_name
        )

    @staticmethod
    def xdcr_replicate(shell_path, source_hostname, source_port, source_username, source_bucket_name, target_bucket_name, cluster_name, hostname, port, username):
        return "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --create --xdcr-from-bucket {source_bucket_name} --xdcr-to-bucket {target_bucket_name} --xdcr-cluster-name {cluster_name}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            source_bucket_name=source_bucket_name,
            target_bucket_name=target_bucket_name,
            cluster_name=cluster_name
        )

    @staticmethod
    def get_replication_uuid(shell_path, source_hostname, source_port, source_username):
        return "{shell_path} xdcr-setup --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --list".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
        )

    @staticmethod
    def get_stream_id(shell_path, source_hostname, source_port, source_username, cluster_name):
        return "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --xdcr-cluster-name {cluster_name} --list".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            cluster_name=cluster_name
        )

    @staticmethod
    def pause_replication(shell_path, source_hostname, source_port, source_username, cluster_name, id):
        return "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --xdcr-cluster-name {cluster_name} --pause --xdcr-replicator={id}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            cluster_name=cluster_name,
            id=id
        )

    @staticmethod
    def resume_replication(shell_path, source_hostname, source_port, source_username, cluster_name, id):
        return "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port}  --username {source_username} --password $source_password --xdcr-cluster-name {cluster_name} --resume --xdcr-replicator={id}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            cluster_name=cluster_name,
            id=id
        )

    @staticmethod
    def delete_replication(shell_path, source_hostname, source_port, source_username, id, cluster_name):
        return "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --delete --xdcr-replicator {id} --xdcr-cluster-name {cluster_name}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            id=id,
            cluster_name=cluster_name
        )

    @staticmethod
    def xdcr_delete(shell_path, source_hostname, source_port, source_username, hostname, port, username, cluster_name):
        return "{shell_path} xdcr-setup --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --delete --xdcr-hostname {hostname}:{port} --xdcr-username {username} --xdcr-password $password --xdcr-cluster-name {cluster_name}".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
            hostname=hostname,
            port=port,
            username=username,
            cluster_name=cluster_name
        )

    @staticmethod
    def get_source_bucket_list(shell_path, source_hostname, source_port, source_username):
        return "{shell_path} bucket-list --cluster {source_hostname}:{source_port} --username {source_username} --password $password -o json".format(
            shell_path=shell_path,
            source_hostname=source_hostname,
            source_port=source_port,
            source_username=source_username,
        )

    @staticmethod
    def get_status(shell_path, hostname, port, username):
        return "{shell_path} server-info --cluster {hostname}:{port} --username {username} --password $password".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username
        )

    @staticmethod
    def node_init(shell_path, port, username, mount_path):
        return "{shell_path} node-init  --cluster 127.0.0.1:{port} --username {username} --password $password --node-init-data-path {mount_path}/data  --node-init-index-path {mount_path}/data --node-init-analytics-path {mount_path}/data  --node-init-hostname 127.0.0.1".format(
            shell_path=shell_path, port=port, username=username, mount_path=mount_path
        )

    @staticmethod
    def bucket_edit(shell_path, hostname, port, username, bucket_name, flush_value):
        return "{shell_path} bucket-edit --cluster {hostname}:{port} --username {username} --password $password --bucket={bucket_name} --enable-flush {flush_value}".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username, bucket_name=bucket_name,
            flush_value=flush_value
        )

    @staticmethod
    def bucket_edit_ramquota(shell_path, hostname, port, username, bucket_name, ramsize):
        return "{shell_path} bucket-edit --cluster {hostname}:{port} --username {username} --password $password --bucket={bucket_name} --bucket-ramsize {ramsize}".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username, bucket_name=bucket_name,
            ramsize=ramsize
        )

    @staticmethod
    def bucket_delete(shell_path, hostname, port, username, bucket_name):
        return "{shell_path} bucket-delete --cluster {hostname}:{port} --username {username} --password $password  --bucket={bucket_name}".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username, bucket_name=bucket_name
        )

    @staticmethod
    def bucket_flush(shell_path, hostname, port, username, bucket_name):
        return "echo 'Yes' | {shell_path}  bucket-flush --cluster {hostname}:{port} --username {username} --password $password --bucket={bucket_name}".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username, bucket_name=bucket_name
        )

    @staticmethod
    def bucket_create(shell_path, hostname, port, username, bucket_name, ramsize, evictionpolicy, bucket_type, bucket_compression):
        return "{shell_path} bucket-create --cluster 127.0.0.1:{port} --username {username} --password $password --bucket {bucket_name} --bucket-type {bucket_type} --bucket-ramsize {ramsize} --bucket-replica 0 --bucket-eviction-policy {evictionpolicy} {bucket_compression} --conflict-resolution sequence --wait".format(
            shell_path=shell_path, port=port, username=username,
            bucket_name=bucket_name, ramsize=ramsize, evictionpolicy=evictionpolicy,
            bucket_type=bucket_type, bucket_compression=bucket_compression
        )

    @staticmethod
    def bucket_list(shell_path, hostname, port, username):
        return "{shell_path} bucket-list --cluster {hostname}:{port} --username {username} --password $password".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username,
        )

    @staticmethod
    def get_indexes_name(hostname, port, username):
        return "curl {username}:$password@{hostname}:{port}/indexStatus".format(
            hostname=hostname, port=port, username=username
        )

    @staticmethod
    def build_index(base_path, hostname, port, username, index_def):
        return "{base_path}/cbq -e {hostname}:{port} -u {username} -p $password -q=true -s='{index_def}'".format(
            base_path=base_path, hostname=hostname, port=port, username=username, index_def=index_def
        )

    @staticmethod
    def is_build_completed(base_path, hostname, port, username, index):
        return "{base_path}/cbq -e {hostname}:{port} -u {username} -p $password -q=true -s=\"SELECT COUNT(*) as unbuilt FROM system:indexes WHERE keyspace_id ={index} AND state <> 'online'".format(
            base_path=base_path, hostname=hostname, port=port, username=username, index=index
        )

    @staticmethod
    def cb_backup_full(base_path, backup_location, backup_repo, hostname, port, username, csv_bucket_list):
        return "{base_path}/cbbackupmgr restore --archive {backup_location} --repo {backup_repo} --cluster couchbase://{hostname}:{port} --username {username} --password $password --force-updates --no-progress-bar --include-buckets {csv_bucket_list}".format(
            base_path=base_path,
            backup_location=backup_location,
            backup_repo=backup_repo,
            hostname=hostname,
            port=port,
            username=username,
            csv_bucket_list=csv_bucket_list
        )

    @staticmethod
    def monitor_replication(source_username, source_hostname, source_port, bucket_name, uuid):
        return "curl --silent -u {source_username}:$password http://{source_hostname}:{source_port}/pools/default/buckets/{bucket_name}/stats/replications%2F{uuid}%2F{bucket_name}%2F{bucket_name}%2Fchanges_left".format(
            source_username=source_username,
            source_hostname=source_hostname,
            source_port=source_port,
            bucket_name=bucket_name,
            uuid=uuid,
        )

    @staticmethod
    def server_info(shell_path, hostname, port, username):
        return "{shell_path} server-info --cluster {hostname}:{port} --username {username} --password $password ".format(
            shell_path=shell_path, hostname=hostname, port=port, username=username
        )


class CommandFactory(DatabaseCommand, OSCommand):
    def __init__(self):
        DatabaseCommand.__init__(self)
        OSCommand.__init__(self)


if __name__ == "__main__":
    print("\n****Test Above Commands With Dummy Values****\n")
    install_path = "DummyInstallPath"
    binary_path = "/opt/couchbase/bin"
    shell_path = "/opt/couchbase/bin"
    hostname = "hostname"
    port = "8091"
    username = "USER"
    cluster_name = "delphix_cluster"
    cluster_ramsize = "200"
    cluster_index_ramsize = "300"
    cluster_fts_ramsize = "400"
    cluster_eventing_ramsize = "500"
    cluster_analytics_ramsize = "600"
    additional_services = "query,index,data"
    source_hostname = "source_hostname"
    source_port = "source_port"
    source_username = "source_username"
    source_bucket_name = "source_bucket_name"
    target_bucket_name = "target_bucket_name"
    uuid = "12345678"
    directory_path = "/mnt/provision/test/directory_path"
    mount_path = "/mnt/provision/mount_path"
    bucket_name = "sample"
    flush_value = "0"
    ramsize = "100"
    evictionpolicy = "evictionpolicy"
    base_path = "base_path"
    index = "index"
    index_name = "index_name"
    backup_location = "backup_location"
    backup_repo = "backup_repo"
    csv_bucket_list = "csv_bucket_list"
    filename = "filename"
    file_path = "test"
    data = "data"
    hostname = "192.168.1.14"
    dir_path = "/var/tmp"
    DLPX_BIN_JQ = "/var/tmp"
    print "find_install_path: ", CommandFactory.find_install_path(binary_path), "\n"
    print "find_binary_path: ", CommandFactory.find_binary_path(), "\n"
    print "find_install_path: ", CommandFactory.find_install_path(binary_path), "\n"
    print "get_process: ", CommandFactory.get_process(), "\n"
    print "get_version: ", CommandFactory.get_version(install_path), "\n"
    print "start_couchbase: ", CommandFactory.start_couchbase(install_path), "\n"
    print "get_data_directory: ", CommandFactory.get_data_directory("couchbase_base_dir"), "\n"
    print "install_path: ", CommandFactory.stop_couchbase(install_path), "\n"
    print "cluster_init: ", CommandFactory.cluster_init(shell_path, hostname, port, username, cluster_ramsize,
                                                        cluster_name, cluster_index_ramsize, cluster_fts_ramsize,
                                                        cluster_eventing_ramsize, cluster_analytics_ramsize,
                                                        additional_services), "\n"
    print "cluster_setting: ", CommandFactory.cluster_setting(shell_path, hostname, port, username, cluster_ramsize,
                                                              cluster_name, cluster_index_ramsize, cluster_fts_ramsize,
                                                              cluster_eventing_ramsize, cluster_analytics_ramsize), "\n"
    print "xdcr_setup: ", CommandFactory.xdcr_setup(shell_path, source_hostname, source_port, source_username, hostname,
                                                    port, username, cluster_name), "\n"
    print "xdcr_replicate: ", CommandFactory.xdcr_replicate(shell_path, source_hostname, source_port, source_username,
                                                            source_bucket_name, target_bucket_name, cluster_name), "\n"
    print "get_replication_uuid :", CommandFactory.get_replication_uuid(shell_path, source_hostname, source_port,
                                                                        source_username), "\n"
    print "get_stream_id:", CommandFactory.get_stream_id(shell_path, source_hostname, source_port, source_username,
                                                         cluster_name), "\n"
    print "pause_replication:", CommandFactory.pause_replication(shell_path, source_hostname, source_port,
                                                                 source_username, cluster_name, uuid), "\n"
    print "resume_replication:", CommandFactory.resume_replication(shell_path, source_hostname, source_port,
                                                                   source_username, cluster_name, uuid), "\n"
    print "delete_replication:", CommandFactory.delete_replication(shell_path, source_hostname, source_port,
                                                                   source_username, uuid, cluster_name), "\n"
    print "xdcr_delete:", CommandFactory.xdcr_delete(shell_path, source_hostname, source_port, source_username,
                                                     hostname, port, username, cluster_name), "\n"
    print "get_source_bucket_list:", CommandFactory.get_source_bucket_list(shell_path, source_hostname, source_port,
                                                                           source_username), "\n"
    print "get_status: ", CommandFactory.get_status(shell_path, hostname, port, username), "\n"
    print "change_permission: ", CommandFactory.change_permission(directory_path), "\n"
    print "make_directory: ", CommandFactory.make_directory(directory_path), "\n"
    print "get_config_directory: ", CommandFactory.get_config_directory(mount_path), "\n"
    print "node_init:", CommandFactory.node_init(shell_path, port, username, mount_path), "\n"
    print "bucket_edit: ", CommandFactory.bucket_edit(shell_path, hostname, port, username, bucket_name,
                                                      flush_value), "\n"
    print "bucket_edit_ramquota: ", CommandFactory.bucket_edit_ramquota(shell_path, hostname, port, username,
                                                                        bucket_name, ramsize), "\n"
    print "bucket_delete: ", CommandFactory.bucket_delete(shell_path, hostname, port, username, bucket_name), "\n"
    print "bucket_flush: ", CommandFactory.bucket_flush(shell_path, hostname, port, username, bucket_name), "\n"
    print "bucket_create: ", CommandFactory.bucket_create(shell_path, hostname, port, username, bucket_name, ramsize,
                                                          evictionpolicy), "\n"
    print "bucket_list: ", CommandFactory.bucket_list(shell_path, hostname, port, username), "\n"
    print "get_indexes_name: ", CommandFactory.get_indexes_name(base_path, hostname, port, username, index), "\n"
    print "build_index: ", CommandFactory.build_index(base_path, hostname, port, username, index_name), "\n"
    print "is_build_completed: ", CommandFactory.is_build_completed(base_path, hostname, port, username, index), "\n"
    print "cb_backup_full: ", CommandFactory.cb_backup_full(base_path, backup_location, backup_repo, hostname, port,
                                                            username, csv_bucket_list), "\n"
    print "monitor_replication: ", CommandFactory.monitor_replication(source_username, source_hostname, source_port,
                                                                      bucket_name, uuid), "\n"
    print "server_info: ", CommandFactory.server_info(shell_path, hostname, port, username), "\n"

    print "read_file: ", CommandFactory.read_file(filename), "\n"

    print "write_file: ", CommandFactory.write_file(filename, data), "\n"

    print "check_file: ", CommandFactory.check_file(file_path), "\n"

    print "get_ip_of_hostname: ", CommandFactory.get_ip_of_hostname(hostname), "\n"

    print "check_directory: ", CommandFactory.check_directory(dir_path), "\n"

    print "delete_file: ", CommandFactory.delete_file(filename), "\n"

    print "get_dlpx_bin: ", CommandFactory.get_dlpx_bin(), "\n"

    print "unmount_file_system: ", CommandFactory.unmount_file_system(mount_path), "\n"
