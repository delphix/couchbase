![](images/image1.png) 








## 
## What Does a Delphix Plugin Do?
Delphix is a data management platform that provides the ability to securely copy and share datasets. Using virtualization, you will ingest your data sources and create virtual data copies, which are full read-write capable database instances that use a small fraction of the resources a normal database copy would require. The Delphix engine has built-in support for interfacing with certain types of datasets, such as Oracle, SQL Server and ASE.

The Delphix virtualization SDK (https://github.com/delphix/virtualization-sdk) provides an interface for building custom data source integrations for the Delphix Dynamic Data Platform. The end users can design/implement a custom plugin which enable them to use custom data source like MongoDB, Cassandra, Couchbase or something else similar to as if they are using a built-in dataset type with Delphix Engine.

## Couchbase Plugin
Couchbase plugin is developed to virtualize couchbase data source leveraging the following built-in couchbase technologies:
  - Cross Data Center Replication (XDCR) allows data to be replicated across clusters that are potentially located in different data centers.
  - Cbbackupmgr allows data to be restored on staging host of Couchbase Server. 
  - Ingest Couchbase: Dsource can be created from a Couchbase cluster/single instance using (XDCR ingestion mechanism) or 
                    : Dsource can be created by restoring from a Couchbase backup peice using (CBBACKUPMGR ingestion mechanism) - Zero Touch Production.
  - Environment Discovery: Couchbase plugin can discover environments where Couchbase server is installed.
  - VDB Creation: Single node Couchbase VDB can be provisioned from the dsource snapshot.


### Table of Contents
1. [Prerequisites](#requirements-plugin)
2. [Build and Upload Plugin](#upload-plugin)
3. [Virtualizing Couchbase](#user-documentation)
4. [Download logs](#run_unit_test_case)
5. [Tested Versions](#tested-versions)
6. [Supported Features](#support-features)
7. [Unsupported Features](#unsupported-features)
8. [Known Issues](#known_issue)
9.  [How to Contribute](#contribute)
10.  [Statement of Support](#statement-of-support)
11.  [License](#license)


### <a id="requirements-plugin"></a>Prerequisites
**Source Requirements:** Couchbase database user with following privileges
*   XDCR_ADMIN
*   DATA_MONITOR

**Staging Requirements**: O/S user with following privileges
1. Regular o/s user.
2. Execute access on couchbase binaries [ chmod -R 775 /opt/couchbase ]
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]
4. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and act as base folder for nfs mounts.
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.
    ```shell
    Defaults:delphixos !requiretty
    delphixos ALL=NOPASSWD: \ 
    /bin/mount, /bin/umount
    ```
6. Customers who intends to use CBBACKUPMGR (Couchbase backup manager ingestion) must follow the instructions to avoid source/production server dependency.

    * Provide all source server buckets related information( using below command ) in a file and place at `<Toolkit-Directory-Path>/couchbase_src_bucket_info.cfg`:
  
       `/opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091  --username $username --password $password`
    
    * Create config file using below command. This file will be required at the time of dSource creation using CBBACKUPMGR.
      `/opt/couchbase/bin/cbbackupmgr config --archive /u01/couchbase_backup --repo delphix`
    
    * Get data from source host in backup directory of staging host
    `/opt/couchbase/bin/cbbackupmgr backup -a /u01/couchbase_backup -r delphix -c couchbase://<hostname> -u user -p password`
       
  

**Target Requirements**: O/S user with following privileges
1. Regular o/s user.
2. Execute access on couchbase binaries [ chmod -R 775 /opt/couchbase ]
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]
4. Empty folder on host to mount nfs filesystem. This is just and empty folder with no space requirements and act as base folder for nfs mounts.
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.
    ```shell
    Defaults:delphixos !requiretty
    delphixos ALL=NOPASSWD: \ 
    /bin/mount, /bin/umount
    ```

### <a id="upload-plugin"></a>Steps to build, upload and run unit tests for plugin
  1. Create a virtual environment and install required libraries(dvp, pytest, pytest-html & pytest-cov) using script `virtualEnvSetup.sh`.
    
  ```bash
    cd <complete path of project directory till `src` directory>
    ./test/virtualEnvSetup.sh <virtual enviornment name>
For example:
    cd /Users/<your-user-name>/Desktop/Plugins/OpenSourceCouchbase/couchbase-plugin
    ./test/virtualEnvSetup.sh "MyLocalEnv"
```
    
  2.  Run this command to activate the virtual environment created in step 1:
   ```bash
    . test/MyLocalEnv/bin/activate
   ```

  3.  Build the source code. It generates the build with name `artifacts.json`:
```bash
    dvp build
```
    
   4. Upload the `artifacts.json` ( generated in step 3 ) on Delphix Engine:
```bash
    dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>
```
   5. Unit test run: Make sure to build the source code( using `dvp build` ) before running unit tests
  ```bash
     pytest test/
```

### <a id="user-documentation"></a> How to Virtualize Couchbase
The following document provides details on how to virtualize couchbase dataset, step-by-step information on how to link, provision couchbase dataset: [CouchbaseUserDocumentation.md](https://github.com/delphix/couchbase-plugin/blob/master/CouchbaseUserDocumentation.md)

### <a id="run_unit_test_case"></a>Download plugin logs
#### Plugin Logs:
Download the plugin logs using below command:

```dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>```

#### Unit test logs: 
##### SummaryReport:
A report with name `Report.html` gets generated in `test` directory which contains the summary of test passed vs failed. If any test case fails then complete stack trace can be seen in that test case section.
##### Module wise coverage report:
There is a report folder `CodeCoverage`(can change the folder name in config file `pytest.ini`) generated in `test` directory, which contains html files. These files help in source code coverage visualization, in which we can see statements processed and missed in each module of source code.



### <a id="tested-versions"></a>Tested Versions
- Delphix Engine: 5.3.x and 6.0.x
- Couchbase Version: 5.5 and 6.0
- Linux Version: RHEL 7.x

### <a id="support-features"></a>Supported Features
- XDCR (Cross Data Center Replication)
- Couchbase Backup Manager

### <a id="unsupported-features"></a>Unsupported Features
- Backup documents as compressed
- Incremental Backup Restore

### <a id="known_issue"></a>Known Issues
- Unable to build indexes during VDB provision

### <a id="contribute"></a>How to Contribute

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) to understand the pull requests process.

### <a id="statement-of-support"></a>Statement of Support

This software is provided as-is, without warranty of any kind or commercial support through Delphix. See the associated license for additional details. Questions, issues, feature requests, and contributions should be directed to the community as outlined in the [Delphix Community Guidelines](https://delphix.github.io/community-guidelines.html).

### <a id="license"></a>License

This is code is licensed under the Apache License 2.0. Full license is available [here](./LICENSE).

