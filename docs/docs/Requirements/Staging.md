## Staging environment 

1. Couchbase binaries installed and configured:
    * disable a auto start using OS services 

        `systemctl disable couchbase-server.service`  
        `systemctl stop couchbase-server.service`

2. Regular o/s user - ex. `delphix_os`
3. Add OS user to `couchbase` OS group
4. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ].
5. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and acts as a base folder for NFS mounts.
6. sudo privileges for mount and umount. See sample below assuming `delphix_os` is used as delphix user.
   ```
   Defaults:delphixos !requiretty
   delphixos ALL=NOPASSWD: \ 
   /bin/mount, /bin/umount
   ```
7. If Couchbase service is installed using `couchbase` user, Delphix OS user ex. `delphix_os` has to be able to run any command as `couchbase` using sudo
   ```
   delphix_os ALL=(couchbase) NOPASSWD: ALL
   ```
8. Additional Utilities required on staging host:
    * ```expect```


## Additional prerequisites for XDCR ingestion

Production Couchbase database user with the following provileges

*  XDCR_ADMIN
*  DATA_MONITOR

If source is a Community Edition, a production Couchbase database user has to be a full admin privilege
to be able to create and monitor XDCR replication

## Additional prerequisites for backup ingestion

Access to an existing backup on the staging server. 
If access is provided over NFS to an existing backup (ex. mount path is /u01/couchbase_backup ) and repository is called PROD the following command have to succeed:

 `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo PROD`

If a new backup will configured on the staging host, the following commands should be executed. Ex. backup location `/u01/couchbase_backup`, repository name `delphix`

* Create config file using the following command. This file will be required at the time of dSource creation using CBBACKUPMGR.   
    `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`

* Bring backup of the production system:   
    * Copy an existing backup
    * Backup from source host into backup directory of staging host  
    `/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<production server> -u user -p password`
