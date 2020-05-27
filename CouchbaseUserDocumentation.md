![](images/image1.png)







Couchbase EDSI Plugin - Install/Configure on Delphix Engine




Table of Contents
=================

[Table of Contents](#table-of-contents)

[Purpose](#purpose)

[Prerequisites](#prerequisites)

[Install Couchbase EDSI Plugin](#install-couchbase-edsi-plugin)

[Refresh Environment](#refresh-environment)

[Create Sourceconfig](#create-sourceconfig)

[Create dSource](#create-dsource)

[XDCR Method](#xdcr-method)

[Couchbase Backup Manager Method](#couchbase-backup-manager-method)

[Provision VDB](#provision-vdb)

[Known Issues](#known-issues)

[Simultaneous dSource creation](#simultaneous-dsource-creation)
 

Purpose
=======

This document contains the screenshot of the steps required to install and configure the couchbase plugin. With the help of these steps can create dSource and VDB.

Prerequisites
=============

-   Install delphix engine 5.3.x and above

-   Install couchbase binaries on source, staging and target servers

Install Couchbase EDSI Plugin
=============================

![](images/image2.png)

![](images/image3.png)

![](images/image4.png)

![](images/image5.png)

![](images/image6.png)

![](images/image7.png)

![](images/image8.png)

Refresh Environment
===================

![](images/image9.png)

Create Sourceconfig
===================

![](images/image10.png)

![](images/image11.png)

Create dSource
==============

 XDCR Method
-----------

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

Provision VDB
=============

![](images/image24.png)
![](images/image25.png)
![](images/image26.png)
![](images/image27.png)


Known Issues
------------

### Simultaneous dSource creation

![](images/image28.png)

![](images/image29.png)
