---
id: Installation
title: Installation
---


[Prerequisites](#prerequisites)

[How To install plugin](#provision-vdb)

 
 
Prerequisites
=============

-   Install delphix engine 5.3.x and above

-   Install couchbase binaries on source, staging and target servers


Install Couchbase Plugin
========================

Using GUI
----------

1. Click on Manage and then Plugins


![](/couchbase-plugin/img/image2.png)

2. Click on `+` icon

![](/couchbase-plugin/img/image3.png)

3. Click on Upload or Upgrade a plugin

![](/couchbase-plugin/img/image4.png)

4. Select the `build(artifacts.json)` 

![](/couchbase-plugin/img/image5.png)

5. Click on close button

![](/couchbase-plugin/img/image6.png)

6. See the plugin version in `Plugins` section

![](/couchbase-plugin/img/image7.png)


Using dvp command
-----------------
 `dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>`


Delphix Engine's documentation on installing plugins: [PluginManagement](https://docs.delphix.com/docs/datasets/unstructured-files-and-app-data/delphix-engine-plugin-management)