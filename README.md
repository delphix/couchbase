<<<<<<< HEAD
# Project Title

One Paragraph of project description goes here

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://github.com/delphix/.github/blob/master/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Joe Smith** - *Initial work* - [Company](https://github.com/Company)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the XX License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
=======
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

### TESTED VERSIONS
- Tested with couchbase 5.5/6.0 on Linux 7


>>>>>>> Creating mater branch
