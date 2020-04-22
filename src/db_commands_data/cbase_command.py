#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

# CommandHandler class contains all commands required to perform couchbase operations.
# No other executable can update this class data, so that we made it only readable using inheritance of ReadOnlyDict class
# We get the required command using dictionary (__commands) and fill the parameters passed by VSDK.


class ReadOnlyDict(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("This information/dictionary is used across toolkit. Can't allow to update ")
    __setitem__ = __readonly__
    __delitem__ = __readonly__

class CommandHandler:
    def __init__(self):
        self.__commands = {
            'find_binary_path' : "echo $COUCHBASE_PATH",
            'find_install_path' : "find {binary_path} -name couchbase-server",
            'find_shell_path' : "find {binary_path} -name couchbase-cli",
            'get_version' : "{install_path} --version",
            'get_process' : "ps -ef",
            'get_data_directory' : "cat {couchbase_base_dir}/etc/couchbase/static_config|grep path_config_datadir",
            'start_couchbase': "{install_path} \-- -noinput -detached .",
            'stop_couchbase': "{install_path} -k",
            'cluster_init': "{shell_path} cluster-init --cluster {hostname}:{port} \
                --cluster-username {username} --cluster-password $password \
                --cluster-ramsize {cluster_ramsize} \
                --cluster-name {cluster_name} \
                --cluster-index-ramsize {cluster_index_ramsize} \
                --cluster-fts-ramsize {cluster_fts_ramsize} \
                --cluster-eventing-ramsize {cluster_eventing_ramsize} \
                --cluster-analytics-ramsize {cluster_analytics_ramsize} \
                --services data,index,{additional_services}",
            'cluster_setting': "{shell_path} setting-cluster -c {hostname}:{port} \
                                                -u {username} \
                                                -p $password \
                                                --cluster-ramsize {cluster_ramsize} \
                                                --cluster-name {cluster_name} \
                                                --cluster-index-ramsize {cluster_index_ramsize} \
                                                --cluster-fts-ramsize {cluster_fts_ramsize} \
                                                --cluster-eventing-ramsize {cluster_eventing_ramsize} \
                                                --cluster-analytics-ramsize {cluster_analytics_ramsize}",
            'xdcr_setup': "{shell_path} xdcr-setup \
                                                --cluster {source_hostname}:{source_port} \
                                                --username {source_username} \
                                                --password $source_password \
                                                --create \
                                                --xdcr-hostname {hostname}:{port} \
                                                --xdcr-username {username} \
                                                --xdcr-password $password \
                                                --xdcr-cluster-name {cluster_name}",
            'xdcr_replicate': "{shell_path} xdcr-replicate \
                                                --cluster {source_hostname}:{source_port} \
                                                --username {source_username} \
                                                --password $source_password \
                                                --create \
                                                --xdcr-from-bucket {source_bucket_name} \
                                                --xdcr-to-bucket {target_bucket_name} \
                                                --xdcr-cluster-name {cluster_name}",
            'get_replication_uuid': "{shell_path} xdcr-setup --cluster {source_hostname}:{source_port} --username {source_username} --password $source_password --list",
            'get_stream_id': "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} \
                                                        --username {source_username} \
                                                        --password $source_password \
                                                        --xdcr-cluster-name {cluster_name} --list",
            'pause_replication': "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} \
                                                --username {source_username} \
                                                --password $source_password \
                                                --xdcr-cluster-name {cluster_name} --pause --xdcr-replicator={id}",
            'resume_replication': "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} \
                                                --username {source_username} \
                                                --password $source_password \
                                                --xdcr-cluster-name {cluster_name} --resume --xdcr-replicator={id}",
            'delete_replication': "{shell_path} xdcr-replicate --cluster {source_hostname}:{source_port} \
                                                --username {source_username} --password $source_password --delete \
                                                --xdcr-replicator {id} --xdcr-cluster-name {cluster_name}",
            'xdcr_delete': "{shell_path} xdcr-setup --cluster {source_hostname}:{source_port} \
                                        --username {source_username} --password $source_password --delete \
                                        --xdcr-hostname {hostname}:{port} --xdcr-username {username} --xdcr-password $password \
                                        --xdcr-cluster-name {cluster_name}",
            'get_source_bucket_list': "{shell_path} bucket-list --cluster {source_hostname}:{source_port} \
                                            --username {source_username} --password $password",
            'get_status': "{shell_path} server-info --cluster {hostname}:{port} --username {username} --password $password",
            'make_directory': "mkdir -p {directory_path}",
            'change_permission': "chmod -R 775 {directory_path}",
            'node_init': "{shell_path} node-init  --cluster 127.0.0.1:{port} \
                                                        --username {username} --password $password\
                                                        --node-init-data-path {mount_path}/data  --node-init-index-path {mount_path}/data\
                                                        --node-init-analytics-path {mount_path}/data  --node-init-hostname 127.0.0.1",
            'bucket_edit': "{shell_path} bucket-edit --cluster {hostname}:{port}\
                                                        --username {username} --password $password --bucket={bucket_name} --enable-flush {flush_value}",
            'bucket_edit_ramquota': "{shell_path} bucket-edit --cluster {hostname}:{port}\
                                                        --username {username} --password $password --bucket={bucket_name} --bucket-ramsize {ramsize}",                                                        
            'bucket_delete': "{shell_path} bucket-delete --cluster {hostname}:{port}\
                                                         --username {username} --password $password  --bucket={bucket_name}",
            'bucket_flush': "echo 'Yes' | {shell_path}  bucket-flush --cluster {hostname}:{port}\
                                                         --username {username} --password $password --bucket={bucket_name}",
            'bucket_create': "{shell_path} bucket-create --cluster 127.0.0.1:{port} --username {username}\
                                                        --password $password --bucket {bucket_name} --bucket-type couchbase\
                                                        --bucket-ramsize {ramsize} --bucket-replica 0 --bucket-eviction-policy\
                                                        {evictionpolicy} --compression-mode passive --conflict-resolution sequence --wait",
            'bucket_list': "{shell_path} bucket-list --cluster {hostname}:{port} --username {username}\
                                                        --password $password",
            'get_config_directory': "{mount_path}/.delphix",
            'get_indexes_name': "{base_path}/cbq -e {hostname}:{port} -u {username} -p $password -q=true -s=\"SELECT\
                                                       name FROM system:indexes where keyspace_id = {index} AND state = 'deferred'\"",
            'build_index': " {base_path}/cbq -e 127.0.0.1:8091 -u {username} -p {password} -q=true\
                                                        -s=echo \"BUILD INDEX ON {index_name}\" {index_name}",
            'is_build_completed': "{base_path}/cbq -e {hostname}:{port} -u {username} -p {password} -q=true -s=\"SELECT\
                                                         COUNT(*) as unbuilt FROM system:indexes WHERE keyspace_id ={index} AND state <> 'online'",
            'cb_backup_full': "{base_path}/cbbackupmgr restore --archive {backup_location} --repo {backup_repo} --cluster couchbase://{hostname}:{port}\
                                                       --username {username} --password $password --force-updates --no-progress-bar --include-buckets {csv_bucket_list}",
            'server_info': "{shell_path} server-info --cluster {hostname}:{port} --username {username} --password $password ",
            'read_file': "cat {filename}",
            'monitor_replication': "curl --silent -u {source_username}:$password http://{source_hostname}:{source_port}/pools/default/buckets/{bucket_name}/stats/replications%2F{uuid}%2F{bucket_name}%2F{bucket_name}%2Fchanges_left",
            'write_file': "echo \'{data}\' > {filename}",
            'check_file': "[ -f {file_path} ] && echo 'Found'",
            'get_ip_of_hostname' : 'hostname -i',
            'check_directory': "[ -d {dir_path} ] && echo 'Found'",
            'delete_file': "rm  -f  {filename}",
            'get_dlpx_bin': "echo $DLPX_BIN_JQ",
            'unmount_file_system' : "sudo /bin/umount {mount_path}",
            'generate_index_script': "curl -s {username}:$password@127.0.0.1:9102/getIndexStatus|$DLPX_BIN_JQ '.status[].definition'|sed -e 's/^\"//g' -e 's/\"$//g' -e 's/`/\\`/g'",
            'get_index_script': "curl -s {username}:$password@127.0.0.1:9102/getIndexStatus|$DLPX_BIN_JQ -r '.status[]|(\"build index on \" + \"`\" + .bucket + \"`\" + \"(\" + .name + \")\")'",
            'execute_index_script': "{base_path}/cbq -e 127.0.0.1:8091 -u {username} -p $password  -q=true -s={index_script}",
            'monitor_build_indexs': "{base_path}/cbq -e 127.0.0.1:8091 -u {username} -p $password -q=true -s=\"SELECT COUNT(*) as unbuilt FROM system:indexes WHERE state <> 'online'\"|$DLPX_BIN_JQ .results[].unbuilt",
        }
        self.__commands = ReadOnlyDict(self.__commands)
    @property
    def commands(self):
        return self.__commands
data =CommandHandler()
