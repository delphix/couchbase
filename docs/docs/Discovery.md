Couchbase EDSI Plugin - Step by step understanding the discovery operation



[Refresh Environment](#refresh-environment)

[Create sourceconfig for XDCR setup](#create-sourceconfig)

[Create sourceconfig for cbbackupmgr setup](#create-dsource)


 

Purpose
=======

Environment discovery is a process that enables the couchbase Plugin to determine couchbase installation details on a host. Database discovery is initiated during the environment set up process.  Whenver there is any changes( installing a new database home )to an already set up environment in the Delphix application, we need to perform environment refresh. 



Prerequisites
=============

-   A source environment must be added to the Delphix Engine

-   Installation of the couchbase Plugin is required before the discovery 

-   Environment variable `$COUCHBASE_PATH ` should be set which contains binary path




Refresh Environment
===================
Environment refresh will update the metadata associated with that environment and sends a new plugin to the host.
Steps: 
1. Login to the Delphix Management application.
2. Click Manage.
3. Select Environments.
4. In the Environments panel, click the name of the environment you want to refresh.
5. Select the Refresh icon.
6. In the Refresh confirmation dialog select Refresh.

![](images/image9.png)



Create Sourceconfig
===================
Environments exist to contain `repositories`, and each environment may have any number of repositories associated with it.
`Repository` contains database instances and in each repository any number of `SourceConfig` objects, which represent known database instances. 
There is no source config generated automatically in couchbase-plugin. Therefore, we need to add `SourceConfig` objects through which can create a dSource. 


For XDCR setup:
Steps: 
1. Login to the Delphix Management application.
2. Click Manage.
3. Select Environments.
4. Select the repository
5. Click on `+` icon ( Shown in next image )
![](images/image10.png)

6. Add required details in pop up
![](images/image11.png)



For CBBKPMGR setup: Here steps is same as we saw in XDCR setup. Since this approach is zero touch production based, no need to fill the exact details of source host. This is bug that source config is coming same for both type of approaches. For now, we can fill dummy data in field of `source host` name.
Steps: 
1. Login to the Delphix Management application.
2. Click Manage.
3. Select Environments.
4. Select the repository
5. Click on `+` icon ( Shown in next image )
![](images/image10.png)

6. Add required details in pop up
![](images/image11.png)


