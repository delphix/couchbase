Build plugin
------------

  1. Create a virtual environment and install required libraries (dvp
  , pytest, pytest-html & pytest-cov) using script `virtualEnvSetup.sh`.
    
  
    `-> cd <complete path of project directory till couchbase-plugin
     directory>`
    
     `-> ./test/virtualEnvSetup.sh <virtual enviornment name>`
    
For example:

    -> cd /Users/<your-user-name>/Desktop/Plugins/OpenSourceCouchbase
    /couchbase-plugin
    -> ./test/virtualEnvSetup.sh "MyLocalEnv"

  2.  Run this command to activate the virtual environment created in step 1.
  
    `. test/MyLocalEnv/bin/activate`

  3.  Build the source code. It generates the build with name `artifact.json`:
  
    `dvp build`

Upload plugin
----------------
   Upload the `artifact.json` (generated in step 3) on Delphix Engine:
```bash
    dvp upload -e <Delphix_Engine_Name> -u <username> --password <password>
```


Unit Test of Plugin code
------------------------
   Unit test run: Make sure to build the source code (using `dvp build
   `) before running unit tests
     ` pytest test/`

Summary Report
---------------
A report with name `Report.html` gets generated in `test` directory which contains the summary of test passed vs failed. If any test case fails then complete stack trace can be seen in that test case section.

Module wise coverage report
---------------------------
There is a report folder `CodeCoverage`(can change the folder name in config file `pytest.ini`) generated in `test` directory, which contains html files. These files help in source code coverage visualization, in which we can see statements processed and missed in each module of source code.


Debug plugin logs
------------------
Download the plugin logs using below command:

```dvp download-logs -c plugin_config.yml -e <Delphix_Engine_Name> -u admin --password <password>```
