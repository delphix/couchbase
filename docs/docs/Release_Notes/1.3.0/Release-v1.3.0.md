<html>
 <head>
<script type="text/JavaScript">
 function Redirect() {
window.location = "https://cd.delphix.com/docs/latest/couchbase-data-sources";
 }
 document.write("You will be redirected to the newer documentation..");
 setTimeout(function() {
Redirect();
 }, 0);
</script>
 </head>
</html>
# Release-v1.3.0

To deploy and configure Couchbase plugin, refer to [Overview](/).

## New & Improved
* CE-540 Bucket size control implementation
* CE-541 Ingestion from multiple full backups
* CE-572 Retry bucket creation if failed
* CE-575 Fix Python error when raising an Exception with traceback.
* CE-325 Record ZFS Storage Calculation Command (Couchbase)

## Additional Requirments related to upgrade
* Not applicable

Future releases may add support for additional OS platforms and Delphix Engine versions.  
