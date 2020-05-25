![](images/image1.png) 

##What Does a Delphix Plugin Do?
Delphix is a data management platform that provides the ability to securely copy and share datasets. Using virtualization, you will ingest your data sources and create virtual data copies, which are full read-write capable database instances that use a small fraction of the resources a normal database copy would require. The Delphix engine has built-in support for interfacing with certain types of datasets, such as Oracle, SQL Server and ASE.

The Delphix virtualization SDK (https://github.com/delphix/virtualization-sdk) provides an interface for building custom data source integrations for the Delphix Dynamic Data Platform. The end users can design/implement a custom plugin which enable them to use custom data source like MongoDB, Cassandra, Couchbase or something else similar to as if they are using a built-in dataset type with Delphix Engine.

##Couchbase Plugin
Couchbase plugin is developed to virtualize couchbase data source leveraging the following built-in couchbase technologies:
  - Cross Data Center Replication (XDCR) allows data to be replicated across clusters that are potentially located in different data centers.
  - Cbbackupmgr allows data to be restored on staging host of Couchbase Server. 
  - Ingest Couchbase: Dsource can be created from a Couchbase cluster/single instance using (XDCR ingestion mechanism) or 
                    : Dsource can be created by restoring from a Couchbase backup peice using (CBBACKUPMGR ingestion mechanism) - Zero Touch Production.
  - Environment Discovery: Couchbase plugin can discover environments where Couchbase server is installed.
  - VDB Creation: Single node Couchbase VDB can be provisioned from the dsource snapshot.


### Table of Contents
1. [Plugin workflow](#pluginworkflow)
2. [Prerequisites](#requirements-)
3. [Build and Upload Plugin](#upload-toolkit)
4. [Virtualizing Couchbase](#user-documentation)
5. [Download logs](#run_unit_test_case)
6. [Tested Versions](#tested-versions)
7. [Supported Features](#support-features)
8. [Unsupported Features](#unsupported-features)
9. [Known Issues](#known_issue)
10.  [How to Contribute](#contribute)
11.  [Statement of Support](#statement-of-support)
12.  [License](#license)


### <a id="pluginworkflow"></a>Plugin workflow

### <a id="Prerequisites"></a>Prerequisites
* macOS 10.14+, Ubuntu 16.04+, or Windows 10
* Python 2.7 (Python 3 is not supported)
* Java 7+
* Delphix Engine 5.3.x / 6.0.x and above

**Source Requirements:** Couchbase database user with following privileges
*   XDCR_ADMIN
*   DATA_MONITOR

**Staging Requirements**: O/S user with following privileges
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
6. Customers who intends to use CBBACKUPMGR (Couchbase backup manager ingestion) must follow the instruction to avoid source/production server dependency.
   - Provide all the source server buckets related information in a text file and place it under the backup location.
   - FilePath : <Toolkit-Directory-Path>/couchbase_src_bucket_info
                In this file add output of below command:
                /opt/couchbase/bin/couchbase-cli bucket-list --cluster <sourcehost>:8091  --username $username --password $pass
                From here all source bucket list information we can fetch and other related data of this bucket should be placed at backup location.
                :param filename: filename(couchbase_src_bucket_info.cfg) where bucket information is kept.

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

### <a id="upload-toolkit"></a>Build plugin, Upload plugin and Unit Test Run
  * Create a virtual environment and install required libraries(dvp, pytest, pytest-html & pytest-cov) using script `virtualEnvSetup.sh`.
    
  ```bash
    cd <complete path of project directory>
    ./virtualEnvSetup.sh <virtual enviornment name>
For example:
    cd /Users/<your-user-name>/Desktop/Plugins/OpenSourceCouchbase/couchbase-plugin
    ./virtualEnvSetup.sh "MyLocalEnv"
```
    
  * Activate the virtualenv:
   ```bash
    . MyLocalEnv/bin/activate
   ```

  *  Build the source code. It generates the build with name of artifacts.json:
```bash
    dvp build
```
    
   * Upload the artifacts.json on Delphix Engine:
```bash
    dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>
```
  * Unit test run:
  ```bash
     pytest
```

### <a id="user-documentation"></a> How to Virtualize Couchbase
The following document provides details on how to virtualize couchbase dataset, step-by-step information on how to link, provision couchbase dataset.
(https://github.com/delphix/couchbase-plugin/blob/master/CouchbaseUserDocumentation.md)

### <a id="run_unit_test_case"></a>Download logs
#### Plugin Logs:
Download the plugin logs using below command:

```dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>```

#### Unit test logs: 
#####SummaryReport:
A report with name `Report.html` generates at project directory which contains the summary of test passed vs failed. If any test case got failed then complete stack trace can be seen in that test case section.
#####Module wise coverage report:
2. There is a report folder `CodeCoverage`(can change the directory name in config file `pytest.ini`) generate which contains html files. Those files helps in source code coverage visualization, in which we can see statements processed and missed in each module of source code.



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

All contributors are required to sign the Delphix Contributor Agreement prior to contributing code to an open source
repository. This process is handled automatically by [cla-assistant](https://cla-assistant.io/). Simply open a pull
request and a bot will automatically check to see if you have signed the latest agreement. If not, you will be prompted
to do so as part of the pull request process.

This project operates under the [Delphix Code of Conduct](https://delphix.github.io/code-of-conduct.html). By
participating in this project you agree to abide by its terms.

### <a id="statement-of-support"></a>Statement of Support

This software is provided as-is, without warranty of any kind or commercial support through Delphix. See the associated license for additional details. Questions, issues, feature requests, and contributions should be directed to the community as outlined in the [Delphix Community Guidelines](https://delphix.github.io/community-guidelines.html).

### <a id="license"></a>License

This is code is licensed under the Apache License 2.0. Full license is available [here](./LICENSE).

