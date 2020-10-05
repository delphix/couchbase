# Discovery


Environment discovery is a process that enables the Couchbase Plugin to determine Couchbase installation details on a host. Database discovery is initiated during the environment set up process
. Whenever there is any change (installing a new database home) to an already set up environment in the Delphix application, we need to perform an environment refresh. 


Prerequisites
=============

-   A source environment must be added to the Delphix Engine.
-   Installation of the Couchbase Plugin is required before the Discovery. 
-   Environment variable `$COUCHBASE_PATH ` should set on staging/target host, which contains the binary path of Couchbase.


Refreshing an Environment
=========================
Environment refresh will update the metadata associated with that environment and send a new Plugin to the host.

1. Login to the **Delphix Management** application.
2. Click **Manage**.
3. Select **Environments**.
4. In the Environments panel, click the name of the environment you want to refresh.
5. Select the **Refresh** icon.
6. In the Refresh confirmation dialog select **Refresh**.

![Screenshot](/couchbase-plugin/image/image9.png)


XDCR Setup
===================
Environments exist to contain `repositories`, and each environment may have any number of repositories associated with it.
`Repository` contains database instances and in each repository any number of `SourceConfig` objects, which represent known database instances. Source config is not generated automatically in
 Couchbase plugin. Therefore, we need to add `SourceConfig` object through which can create a dSource. 

1. Login to the **Delphix Management** application.
2. Click **Manage**.
3. Select **Environments**.
4. Select the repository.
5. Click on **+** icon (Shown in next image).


![Screenshot](/couchbase-plugin/image/image10.png)


6. Add required details in the `Add database` section.
 - Enter port number in **Source Couchbase port** section.
 - Enter source host address in section **Source Host**.
 - Enter unique name for the staging database in **identify field** section.
 - Enter Couchbase data path of staging host in **DB data path** section.


![Screenshot](/couchbase-plugin/image/image11.png)


CBBACKUPMGR Setup
=================

The steps to add source config remain the same as we saw in XDCR setup. In this approach, we don't connect to source environment as this is zero-touch production approach.
We can enter any random or dummy value in this field of source host name when we choose CBBACKUPMGR option for data ingestion.

1. Login to the **Delphix Management** application.
2. Click **Manage**.
3. Select **Environments**.
4. Select the repository.
5. Click on **+** icon (Shown in next image).  
![Screenshot](/couchbase-plugin/image/image10.png)

6. In the **Add Database** section enter the following information:
 - `Source Couchbase port`: This is the port number to be used by Couchbase services.
 - `Source Host`: Leave this field as blank.
 - `identity field`: Provide unique name for staging database.
 - `DB data path`: Leave this field as blank.


![Screenshot](/couchbase-plugin/image/image11.png)



