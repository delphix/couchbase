# Overview

Couchbase plugin is developed to virtualize Couchbase data source. The ingestion (synchronization process) leveraging the following built-in Couchbase technologies
depends on the Couchbase Edition:

- Community Edition:
    - Cross Data Center Replication (XDCR)

- Enterprise Edition:
    - existing backup manged by `cbbackupmgr` tool (Zero production touch ingestion)
    - Cross Data Center Replication (XDCR)


### Cross Data Center Replication (XDCR)

Cross Data Center Replication is a method to replicate date between source and target bucket. Plugin is automatically setting up an one way replication
from a production Couchbase cluster to a staging Couchbase cluster created by Delphix Enging during a dSource ingestion.
Replication to staging server will be added to the existing list of replication and it will be managed by plugin itself.

[link to official XDCR documentation](https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-overview.html)


### Exiting backup ingestion ( `cbbackupmgr` )

Couchbase Enterprise Edition is providing an additional tool called `cbbackupmgr`.
This tool can be leveraged to protect a production Couchbase cluster and an existing backup
will be used to create a staging server. This method allow cloning a production Couchbase cluster
without touching a production server by Delphix Engine nor staging server. In zero production touch
setup staging server has to have access to cbbackupmgr archive folder and repository.

[link to official cbbackupmgr documentation](https://docs.couchbase.com/server/6.6/backup-restore/backup-restore.html)


# Architecture diagrams

### Ingestion using XDCR


![Architecture for XDRC](./image/architecture_xdcr.png)

### Ingestion using backup


![Architecture for cbbackupmgr](./image/architecture_backup.png)

# Support Matrix

![Support matrix Couchbase](./image/compability_couchbase.png)

![Support matrix OS](./image/compability_os.png)


# Prerequisites

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



## Target environment 

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


## Ports

### Ports for XDCR

![Ports for XDCR](./image/ports_xdcr.png)

### Ports for Backup

![Ports for Backup](./image/ports_backup.png)



# Limitations

* Multi-node VDB can't be cloned.
* V2P is not supported
* Point in time recovery is not supported. Provision / refresh / rewind time is based on snapshot only




       
  


    

