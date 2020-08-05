# Linking

[Purpose](#purpose)

[Prerequisites](#prerequisites)

[Create dSource](#create-dsource)

[XDCR Method](#xdcr-method)

[Couchbase Backup Manager Method](#couchbase-backup-manager-method)


Purpose
=======
Linking a data source will create a dSource object on the engine and allow Delphix to ingest data from this source. The dSource is an object that the Delphix Virtualization Engine uses to create and update virtual copies of your database. 



Prerequisites
=============

-   Discovery and source config object should be created on staging host before proceeding to link couchbase dataset 


Create dSource
==============

Steps:

1. Login to Delphix Management application.
2. Click Manage >  Datasets
3. Select Add dSource.
4. In the Add dSource wizard, select the couchbase source config you just created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource type from the drop-down available on dSource wizard.

 XDCR Method
-----------
Cross data center replication allows data to be replicated across clusters that are potentially located in different data centers.


1. Enter the details for "Staging Couchbase host" - FQDN or IP address recommended
2. Enter the details for "Staging Port Number" available on staging host. The default port for couchbase is 8091.
3. Enter the details for "Mount Path" available on staging host. This empty folder acts as a base for NFS mounts.
4. Enter the details for "Staging Cluster Name" you would like Delphix to setup on your staging host.
5. Enter the configuration details for your staging cluster as per resource availability on the staging host.
- Cluster RAM Size
- Cluster Index RAM Size
- Cluster FTS RAM Size
- Cluster Eventing RAM Size
- Cluster Analysis RAM Size

![Screenshot](/couchbase-plugin/image/image12.png)

![Screenshot](/couchbase-plugin/couchbase-plugin/image/image13.png)

6. Click on (+) plus symbol to modify configuration settings. This option allows to include bucket lists which should be part of couchbase cross data center replication (XDCR).

![Screenshot](/couchbase-plugin/image/image14.png)

7. Enter the details of Bucket Name to be part of XDCR.

![Screenshot](/couchbase-plugin/image/image15.png)

8. Provide the details for "dSource Name" and "Target group" on the dSource configuration page.

![Screenshot](/couchbase-plugin/image/image16.png)


9. On the data management page, select the following:
- Staging Environment: This will be your staging host where source config was created.
- User: Database OS user with required privileges for linking the dataset.

10. On the next section, review the configuration and click on next button to review the final summary.

11. Click the submit button which will initiate the linking process.


![Screenshot](/couchbase-plugin/image/image17.png)

12. Once dSource is created successfully, you can review the datasets on Manage > Datasets > dSource Name.

![Screenshot](/couchbase-plugin/image/image19.png)

13. Review the datasets on Manage > Environment > Database section.

![Screenshot](/couchbase-plugin/image/image18.png)


Couchbase Backup Manager Method 
-------------------------------
Follow below instructions before going to create dsource to avoid source/production server dependency.
- Provide source server buckets related information in a file and place at `/tmp/couchbase_src_bucket_info.cfg`
 
  `/opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091 --username $username --password $password`

- Backup Repository: This file will be required at the time of dSource creation using CBBACKUPMGR.
 
  `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`

- Backup Location: Get data from source host in backup directory of staging host

`/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<hostname> -u user -p password`

Steps:

1. Login to Delphix Management application.
2. Click Manage >  Datasets
3. Select Add dSource.
4. In the Add dSource wizard, select the couchbase source config you just created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource type from the drop-down available on dSource wizard.
- Couchbase Backup Manager: Cbbackupmgr allows data to be restored on staging host of Couchbase Server.
7. When we select CBbackupmgr as dSource Type, the following fields on dSource wizard are mandatory.
8. Enter the details for "Backup Location" where the backup files generated through cbbackupmgr are present on the staging host.
9. Enter the details for "Backup Repository" that contains a backup configuration of staging host. Details on how how to setup backup repository are listed here.

Note: When we select dSource Type as Couchbase Backup Manager, we do not require any details for `Staging Couchbase Host` field.
10. Remaining steps for cbbackupmgr ingestion are similar to XDCR.


![Screenshot](/couchbase-plugin/image/image22.png)
![Screenshot](/couchbase-plugin/image/image23.png)


