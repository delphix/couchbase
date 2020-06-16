![](images/image1.png)







Couchbase EDSI Plugin - Step by step understanding the discovery operation




[Refresh Environment](#refresh-environment)

[Create Sourceconfig](#create-sourceconfig)

[Create dSource](#create-dsource)


 

Purpose
=======

Environment discovery is a process that enables the couchbase Plugin to determine couchbase installation details on a host.  
Database discovery is initiated during the environment set up process.  Whenver there is any changes( installing a new database home )to an already set up environment in the Delphix application, we need to perform environment refresh. 


Prerequisites
=============

-   A source environment must be added to the Delphix Engine

-   Installation of the couchbase Plugin is required before the discovery 

-   Environment variable `$COUCHBASE_PATH ` should be set which contains binary path


Refresh Environment
===================
Environment refresh will update the metadata associated with that environment and sends a new plugin to the host.

![](images/image9.png)


Create Sourceconfig
===================

For XDCR setup:

![](images/image10.png)

![](images/image11.png)

For CBBKPMGR setup:

![](images/image10.png)

![](images/image11.png)


