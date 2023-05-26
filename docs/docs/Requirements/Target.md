## Target environment 

1. Couchbase binaries installed and configured:
    * disable a auto start using OS services 

        `systemctl disable couchbase-server.service`  
        `systemctl stop couchbase-server.service`

2. Regular o/s user - ex. `delphix_os`
3. Add OS user to `couchbase` OS group
4. Empty folder on host to hold delphix toolkit  [ approximate 2GB free space ].
5. Empty folder on host to mount nfs filesystem. This is just an empty folder with no space requirements and acts as a base folder for NFS mounts.
6. sudo privileges for mount and umount. See sample below assuming `delphix_os` is used as delphix user.
   ```bash
   Defaults:delphixos !requiretty
   delphixos ALL=NOPASSWD: \ 
   /bin/mount, /bin/umount
   ```
7. If Couchbase service is installed using `couchbase` user, Delphix OS user ex. `delphix_os` has to be able to run any command as `couchbase` using sudo
   ```shell
   delphix_os ALL=(couchbase) NOPASSWD: ALL
   ```
8. Additional Utilities required on staging host:
    * ```expect```
