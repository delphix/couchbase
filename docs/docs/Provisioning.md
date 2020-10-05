# Provisioning

Virtual databases are a virtualized copies of dSource. 

Prerequisites
=============

-   Required a linked dSource from a source host.
-   Added compatible target environment on Delphix Engine.


Provisioning a VDB
==================

1. Click on the icon highlighted in red color.   
![Screenshot](/couchbase-plugin/image/image24.png)

2. Select the target host from the dropdown on which VDB needs to be created.  
![Screenshot](/couchbase-plugin/image/image25.png)

3. Enter the following values for the target configuration:
    - `Target Port Number`: Port number on which Couchbase services will be started.
    - `Mount Path`: NFS mount path where dSource snapshot will be mounted by Engine.
    - `Target Cluster name`: Cluster name which is required to be set up on the target host.
    - `Cluster Ram Size`
    - `Cluster Index Ram Size`
    - `Cluster FTS Ram Size`
    - `Cluster Eventing Ram Size`
    - `Cluster Analytics Ram Size`
    - `Target couchbase Admin User`
    - `Target couchbase Admin password`  
![Screenshot](/couchbase-plugin/image/image26.png)

4. Provision vFiles: Add VDB name and target group.  
![Screenshot](/couchbase-plugin/image/image27.png)

5. No need to add Policies, select **Next**.

6. No need to add Masking, select **Next**.

7. No need to add Hooks, select **Next**.

8. Preview the summary and select **Submit**. 

9. Once the VDB is created successfully, you can review the datasets on **Manage** > **Datasets** > **vdb Name**.
