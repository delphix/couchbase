# Overview

Couchbase plugin is developed to virtualize Couchbase data source leveraging the following built-in couchbase technologies:


- Cross Data Center Replication (XDCR) allows data to be replicated across clusters that are potentially located in different data centers.
- Cbbackupmgr allows data to be restored on staging host of Couchbase Server.

Ingesting Couchbase
----------------

1. Couchbase cluster/single instance using (XDCR ingestion mechanism).
2. Couchbase backup piece using (CBBACKUPMGR ingestion mechanism) - Zero Touch Production.

### <a id="requirements-plugin"></a>Prerequisites
**Source Requirements:** Couchbase database user with the following privileges:

*  XDCR_ADMIN
*  DATA_MONITOR

**Staging Requirements**: O/S user with the following privileges:

1. Couchbase binaries installed and configured:
    * disable a auto start using OS services 

        `systemctl disable couchbase-server.service`  
        `systemctl stop couchbase-server.service`

2. Regular o/s user - ex. `delphix_os`
3. Add OS user to `couchbase` OS group
4. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ].
5. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and acts as a base folder for NFS mounts.
6. sudo privileges for mount and umount. See sample below assuming `delphix_os` is used as delphix user.

   ```bash
   Defaults:delphixos !requiretty
   delphixos ALL=NOPASSWD: \ 
   /bin/mount, /bin/umount
   ```
     
7. If Couchbase service is installed using `couchbase` user, Delphix OS user ex. `delphix_os` has to be able to run any command as `couchbase` using sudo
   ```shell
   delphix_os ALL=(couchbase) NOPASSWD: ALL
   ```
8. Customers who intend to use CBBACKUPMGR (Couchbase backup manager ingestion) must provide access to an existing backup on the staging server. 
   Ex. backup location `/u01/couchbase_backup`, repository name `delphix`
    * Create config file using the following command. This file will be required at the time of dSource creation using CBBACKUPMGR.   
      `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`
    * Bring backup of the production system:   
        * Copy an existing backup
        * Backup from source host into backup directory of staging host   
        `/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<production server> -u user -p password`
       
  

**Target Requirements**: O/S user with the following privileges:

1. Couchbase binaries installed and configured:
    * disable a auto start using OS services 

        `systemctl disable couchbase-server.service`  
        `systemctl stop couchbase-server.service`

2. Regular o/s user - ex. `delphix_os`
3. Add OS user to `couchbase` OS group
4. Empty folder on host to hold Delphix toolkit  `[ approximate 2GB free space ]`.
5. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as a base folder for NFS mounts.
6. sudo privileges for mount and umount. See sample below assuming `delphix_os` is used as delphix user.   

   ```bash
   Defaults:delphixos !requiretty
   delphixos ALL=NOPASSWD: \ 
   /bin/mount, /bin/umount
   ```

7. If Couchbase service is installed using `couchbase` user, Delphix OS user ex. `delphix_os` has to be able to run any command as `couchbase` using sudo
   
      ```
      delphix_os ALL=(couchbase) NOPASSWD: ALL
      ```
    

