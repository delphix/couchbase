As the first step for analysis, we would request the support team to fetch the following custom plugin log files from the customer environment and upload them to the same case along with the support bundle.

# Plugin Logs
Download the Plugin logs using the following methods:

 * Using dvp

    `dvp download-logs -c plugin_config.yml -e FQDN_of_engine -u admin --password`

 * Using GUI

    Help --> Supports Logs --> Plugin Logs --> Download

# Couchbase logs
Couchbase logs are usually located at this path: `/opt/couchbase/var/couchbase/lib/logs` 
and it should be zipped and uploaded together with a support bundle


# Typical issues

 1. Couchbase services not disabled on the new server start - VDB not configured 
    
    After installation or reboot OS may start a Couchbase server without storage allocated from Delphix Engine 
    and Couchbase will create an empty configuration file and allow end user to configure it.
    If Delphix VDB provisioning will be started, Delphix won't be able to kill not configured Couchbase process
    and VDB creation till timeout after 3600 sec.

    Solution:

    - Disable Couchbase services using systemctl, 
    - Kill all Couchbase processes, 
    - Create a VDB using Delphix

 2. Couchbase services not disabled on server start but VDB configured
    
    After reboot OS may start a Couchbase server without storage allocated from Delphix Engine and Couchbase will see 
    an empty data directory. Couchbase server won't report this as an error but rather will recreate all buckets without data.

    Solution:

    - Disable Couchbase services using systemctl, 
    - Kill all Couchbase processes, 
    - Disable force VDB in Delphix Engine, 
    - Enable VDB


 3. Not enough memory on server to restore bucket

    dSource initial ingestion or snapshot is faling with an cbbackmgr transaction error. 
    Check in the Couchbae logs, if this error is realted to a memory allocated for the bucket.

    ```
    2022-01-10T15:39:58.421+01:00 WARN: (Pool) (XXX) Failed to send key '<ud>CL-BAG-C618641009-2</ud>' due to error 'server is out of memory | {"status_code":130,"bucket":"XXX","error_name":"ENOMEM","error_description":"No memory available to store item. Add memory or remove some items and try later"...
    ```

    If this is a case there are to options:

    - For an exiting staging serer, login to staging server Couchbase GUI and change bucket memory configuration
    - For a new ingestion, set a higher memory for all bucket - there is a limitation there as for know Plugin 
      allows to overwrite a memory setting only for all buckets together

