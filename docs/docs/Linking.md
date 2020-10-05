# Linking

Linking a data source will create a dSource object on the engine and allow Delphix to ingest data from this source. The dSource is an object that the Delphix Virtualization Engine uses to create and update virtual copies of your database. 



Prerequisites
=============

Discovery and source config object should be created on the staging host before proceeding to link Couchbase dataset. 


Creating dSource
==============


1. Login to **Delphix Management** application.
2. Click **Manage** >  **Datasets**.
3. Select **Add dSource**.
4. In the Add dSource wizard, select the Couchbase source configuration which is created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource approach from the drop-down (XDCR and Couchbase Backup Manager) available on dSource wizard.
7. Based on approach selection, follow the steps either for XDCR or Couchbase Backup Manager method. The Description of both methods is below.


 Method1: XDCR
--------------
Cross datacenter replication allows data to be replicated across clusters that are potentially located in different data centers.


1. Enter the details for **Staging Couchbase host** - FQDN or IP address recommended.
2. Enter the details for **Staging Port Number** available on the staging host. The default port for couchbase is 8091.
3. Enter the details for **Mount Path** available on the staging host. This empty folder acts as a base for NFS mounts.
4. Enter the details for **Staging Cluster Name** to setup new cluster on the staging host.
5. Enter the configuration details for your staging cluster as per resource availability on the staging host.
    - Cluster RAM Size
    - Cluster Index RAM Size
    - Cluster FTS RAM Size
    - Cluster Eventing RAM Size
    - Cluster Analysis RAM Size              
![Screenshot](/couchbase-plugin/image/image12.png)

6. Click on **+** plus symbol to modify configuration settings. Mention bucket list for which cross datacenter replication (XDCR) only be enabled.  
![Screenshot](/couchbase-plugin/image/image14.png)

7. Enter the details of **Bucket Name** to be part of XDCR. Then click on **Next** button  
![Screenshot](/couchbase-plugin/image/image15.png)

8. Provide the details for **dSource Name** and **Target group** on the dSource configuration page.  
![Screenshot](/couchbase-plugin/image/image16.png)

9. On the **Data management** page, select the following:
    - Staging Environment: This will be your staging host where source config was created.
    - User: Database OS user with required privileges for linking the dataset.
10. On the next section, review the configuration and click on **Next** button to view the summary.
11. Click the **Submit** button which will initiate the linking process.
![Screenshot](/couchbase-plugin/image/image17.png)
12. Once dSource is created successfully, you can review the datasets on **Manage** > **Datasets** > **dSource Name**.  
![Screenshot](/couchbase-plugin/image/image19.png)


Method2: Couchbase Backup Manager 
---------------------------------------
**Note**: Follow the instructions below before creating dSource to avoid source/production server dependency.

- Provide source server buckets related information in a file: */tmp/couchbase_src_bucket_info.cfg*.
  `/opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091 --username $username --password $password`

- **Backup Repository**: This file will be required at the time of dSource creation using CBBACKUPMGR.
  `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`

- **Backup Location**: Get data from source host in backup directory of staging host.
`/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<hostname> -u user -p password`     


**Procedure**:


1. Login to **Delphix Management** application.
2. Click **Manage** >  **Datasets**.
3. Select **Add dSource**.
4. In the **Add dSource wizard**, select the Couchbase source configuration you created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource type from the drop-down available on dSource wizard.
7. When we select CBBACKUPMGR as dSource Type, the following fields on dSource wizard are mandatory.
    - Enter the details for **Backup Location** where the backup files generated through CBBACKUPMGR are present on the staging host.
    - Enter the details for **Backup Repository** that contains a backup configuration of staging host. 
8. The remaining steps for CBBACKUPMGR ingestion are similar to XDCR. Use steps from the second point mentioned in XDCR method. 

Note: When we select dSource type as Couchbase Backup Manager, we do not require any details for the `Staging Couchbase Host` field.

![Screenshot](/couchbase-plugin/image/image22.png)

