# Couchbase Plugin
Table of Contents
* [REQUIREMENTS :](#requirements-)
   * [<em>Source Requirements</em>](#source-requirements)
   * [<em>Staging Requirements</em>](#staging-requirements)
   * [<em>Target Requirements</em>](#target-requirements)
* [TESTED VERSIONS](#tested-versions)
* [SUPPORT FEATURES](#support-features)
* [UNSUPPORTED FEATURES](#unsupported-features)
* [UPLOAD TOOLKIT](#upload-toolkit)
* [MANUAL DISCOVERY PROCESS](#manual-discovery-process)
* [AUTO DISCOVERY PROCESS](#auto-discovery-process)

### REQUIREMENTS :

#### _Source Requirements_

**Couchbase database user with following privileges**
1. XDCR_ADMIN
2. DATA_MONITOR


#### _Staging Requirements_

**O/S user with following privileges**
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

#### _Target Requirements_

**O/S user with following privileges**
1. Regular o/s user.
2. Execute access on couchbase binaries
3. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ]
4. Empty folder on host to mount nfs filesystem. This is just and empty folder with no space requirements and act as base folder for nfs mounts.
5. sudo privileges for mount, umount. See sample below assuming `delphix_os` is used as delphix user.

```shell
Defaults:delphixos !requiretty
delphixos ALL=NOPASSWD: \ 
/bin/mount, /bin/umount
```

#### TESTED VERSIONS
- Tested with couchbase 5.5/6.0 on Linux 7


#### SUPPORT FEATURES
- XDCR, CB backkup manager



