# Linking

Linking a data source will create a dSource object on the engine and allow Delphix to ingest data from this source. The dSource is an object that the Delphix Virtualization Engine uses to create and update virtual copies of your database. 



## Prerequisites

Staging environment created and source database configured in discovered repository

## Creating dSource using XDCR

1. Login to **Delphix Management** application.
2. Click **Manage** >  **Datasets**.
3. Select **Add dSource**.
4. In the Add dSource wizard, select the Couchbase source configuration which is created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource type XDCR from the drop-down available on dSource wizard.
7. Based on approach selection, follow the steps either for XDCR or Couchbase Backup Manager method. The Description of both methods is below.
8. Enter the details for **Staging Couchbase host** - FQDN or IP address recommended.
9. Enter the details for **Staging Port Number** available on the staging host. The default port for couchbase is 8091.
10. Enter the details for **Mount Path** available on the staging host. This empty folder acts as a base for NFS mounts.
11. Enter the details for **Staging Cluster Name** to setup new cluster on the staging host.
12. Enter the configuration details for your staging cluster as per resource availability on the staging host.
    - Cluster RAM Size
    - Cluster Index RAM Size
    - Cluster FTS RAM Size
    - Cluster Eventing RAM Size - this should be 0
    - Cluster Analysis RAM Size - this should be 0    

    ![Screenshot](./image/add_dsource_1.png)

13. Enter the details for **Staging Cluster Admin User**  and **Staging Cluster Admin Password**
14. Enter the details for **Source Cluster Admin User**  and **Source Cluster Admin Password**

    ![Screenshot](./image/add_dsource_2.png)

15. If not all buckets needs to be replicated, click on **+** plus symbol to modify configuration settings. Mention bucket list for which cross datacenter replication (XDCR) only be enabled.  
    ![Screenshot](./image/image14.png)

16. Enter the details of **Bucket Name** to be part of XDCR. Then click on **Next** button  
    ![Screenshot](./image/image15.png)

17. Provide the details for **dSource Name** and **Target group** on the dSource configuration page.  
    ![Screenshot](./image/add_dsource_3.png)

18. On the **Data management** page, select the following:
    - Staging Environment: This will be your staging host where source config was created.
    - User: Database OS user with required privileges for linking the dataset.

    ![Screenshot](./image/add_dsource_4.png)

19. On the next screens, configure a policy, hooks and review the configuration and click on **Next** button to view the summary.

    ![Screenshot](./image/add_dsource_5.png)

    ![Screenshot](./image/add_dsource_6.png)


20. Click the **Submit** button which will initiate the linking process.

    ![Screenshot](./image/add_dsource_7.png)


21. Once dSource is created successfully, you can review the datasets on **Manage** > **Datasets** > **dSource Name**.  


     ![Screenshot](./image/dsource_ingested.png)


## Creating dSource using backup

Prerequisites:
Access to production backup with those ex. values:

/backup - archive

PROD - repository

```
 /opt/couchbase/bin/cbbackupmgr info -a /backup -r PROD
 Name  | Size     | # Backups  |
 PROD  | 58.03MB  | 1          |
 +  Backup                               | Size     | Type  | Source                              | Cluster UUID                      | Range  | Events  | Aliases  | Complete  |
 +  2022-01-10T11_29_26.465860528-05_00  | 58.03MB  | FULL  | http://couchbasesrc.dlpxdc.co:8091  | 08f7937a26b2d20178a5ed16d7a2dd1c  | N/A    | 0       | 0        | true      |
```


1. Login to **Delphix Management** application.
2. Click **Manage** >  **Datasets**.
3. Select **Add dSource**.
4. In the Add dSource wizard, select the Couchbase source configuration which is created on the staging host.
5. Enter the Couchbase-specific parameters for your dSource configuration.
6. Select the dSource type Couchbase Backup Manager from the drop-down available on dSource wizard.
7. Based on approach selection, follow the steps either for XDCR or Couchbase Backup Manager method. The Description of both methods is below.
8. Enter the details for **Staging Couchbase host** - FQDN or IP address recommended.
9. Enter the details for **Staging Port Number** available on the staging host. The default port for couchbase is 8091.
10. Enter the details for **Backup Location** available on the staging host. 
11. Enter the details for **Backup repository** 
12. Enter the details for **Mount Path** available on the staging host. This empty folder acts as a base for NFS mounts.
13. Enter the details for **Staging Cluster Name** to setup new cluster on the staging host.
14. Enter the configuration details for your staging cluster as per resource availability on the staging host.
    - Cluster RAM Size
    - Cluster Index RAM Size
    - Cluster FTS RAM Size
    - Cluster Eventing RAM Size - this should be 0
    - Cluster Analysis RAM Size - this should be 0    

    ![Screenshot](./image/add_dsource_1backup.png)

15. Enter the details for **Staging Cluster Admin User**  and **Staging Cluster Admin Password**
16. Enter dummy values for **Source Cluster Admin User**  and **Source Cluster Admin Password** - they are not used

    ![Screenshot](./image/add_dsource_2backup.png)

17. Then click on **Next** button  

17. Provide the details for **dSource Name** and **Target group** on the dSource configuration page.  
    ![Screenshot](./image/add_dsource_3.png)

18. On the **Data management** page, select the following:
    - Staging Environment: This will be your staging host where source config was created.
    - User: Database OS user with required privileges for linking the dataset.

    ![Screenshot](./image/add_dsource_4.png)

19. On the next screens, configure a policy, hooks and review the configuration and click on **Next** button to view the summary.

    ![Screenshot](./image/add_dsource_5.png)

    ![Screenshot](./image/add_dsource_6.png)


20. Click the **Submit** button which will initiate the linking process.

    ![Screenshot](./image/add_dsource_7backup.png)


21. Once dSource is created successfully, you can review the datasets on **Manage** > **Datasets** > **dSource Name**.  


     ![Screenshot](./image/dsource_ingested.png)

