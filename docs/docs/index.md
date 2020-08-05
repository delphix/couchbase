# Overview

Couchbase plugin is developed to virtualize couchbase data source leveraging the following built-in couchbase technologies:


- Cross Data Center Replication (XDCR) allows data to be replicated across clusters that are potentially located in different data centers.
- Cbbackupmgr allows data to be restored on staging host of Couchbase Server.

Ingest Couchbase
----------------

1. Couchbase cluster/single instance using (XDCR ingestion mechanism) 
2. Couchbase backup peice using (CBBACKUPMGR ingestion mechanism) - Zero Touch Production.

### <a id="requirements-plugin"></a>Prerequisites
**Source Requirements:** Couchbase database user with following privileges

*  XDCR_ADMIN
*  DATA_MONITOR

**Staging Requirements**: O/S user with following privileges

1. Regular o/s user.
2. Execute access on couchbase binaries [ chmod -R 775 /opt/couchbase ]
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]
4. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.
    ```shell
    Defaults:delphixos !requiretty
    delphixos ALL=NOPASSWD: \ 
    /bin/mount, /bin/umount
    ```
6. Customers who intends to use CBBACKUPMGR (Couchbase backup manager ingestion) must follow the instructions to avoid source/production server dependency.

    * Provide all source server buckets related information( using below command ) in a file and place at `<Toolkit-Directory-Path>/couchbase_src_bucket_info.cfg`:
  
       `/opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091  --username $username --password $password`
    
    * Create config file using below command. This file will be required at the time of dSource creation using CBBACKUPMGR.
      
      `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`
    
    * Get data from source host in backup directory of staging host
    
      `/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<hostname> -u user -p password`
       
  

**Target Requirements**: O/S user with following privileges

1. Regular o/s user.
2. Execute access on couchbase binaries [ chmod -R 775 /opt/couchbase ]
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]
4. Empty folder on host to mount nfs filesystem. This is just and empty folder with no space requirements and act as base folder for nfs mounts.
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.

    `Defaults:delphixos !requiretty`

    `delphixos ALL=NOPASSWD: /bin/mount, /bin/umount`
    

