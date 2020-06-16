
#Linking Couchbase Data Source



Table of Contents
=================

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


Enter the details for "Staging Couchbase host" - FQDN or IP address recommended
Enter the details for "Staging Port Number" available on staging host. The default port for couchbase is 8091.
Enter the details for "Mount Path" available on staging host. This empty folder acts as a base for NFS mounts.
Enter the details for "Staging Cluster Name" you would like Delphix to setup on your staging host.
Enter the configuration details for your staging cluster as per resource availability on the staging host.

![](images/image12.png)

![](images/image13.png)

![](images/image14.png)

![](images/image15.png)

![](images/image16.png)

![](images/image17.png)

Complete the wizard and click submit.

![](images/image18.png)

![](images/image19.png)

![](images/image20.png)

 Couchbase Backup Manager Method 
-------------------------------

![](images/image21.png)
![](images/image22.png)
![](images/image23.png)

