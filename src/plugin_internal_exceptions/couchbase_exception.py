#
# Copyright (c) 2020 by Delphix. All rights reserved.
#


from base_exception import DatabaseException

# Some of below defined exceptions are not being used currently but designed for future updates.

# When any database operation is failed and we don't know about this.
class CouchbaseOperationError(DatabaseException):
    def __init__(self, message):
        super(CouchbaseOperationError, self).__init__(message)

# When any server error
class CouchbaseInternalServerError(DatabaseException):
    def __init__(self, message):
        super(CouchbaseInternalServerError, self).__init__(message)

# When Unable to connect to given host
class CouchbaseConnectionError(DatabaseException):
    def __init__(self, message):
        super(CouchbaseConnectionError, self).__init__(message)

# Not able to create mount directory
class MountDataPathCreation(DatabaseException):
    def __init__(self, message):
        super(MountDataPathCreation, self).__init__(message)

# XDCR replication failed
class CouchbaseReplicationProfileError(DatabaseException):
    def __init__(self, message):
        super(CouchbaseReplicationProfileError, self).__init__(message)

# Stream ID deletion error
class StreamIDDeletionError(DatabaseException):
    def __init__(self, message):
        super(StreamIDDeletionError, self).__init__(message)

# XDCR deletion error
class XDCRDeletionError(DatabaseException):
    def __init__(self, message):
        super(XDCRDeletionError, self).__init__(message)

# For bucket related operation like bucket edit, flush, delete, create
class BucketOperationError(DatabaseException):
    def __init__(self, message):
        super(BucketOperationError, self).__init__(message)

# When invalid username and password is provide
class CouchbaseCredentialError(DatabaseException):
    def __init__(self,message):
        super(CouchbaseCredentialError, self).__init__(message)

# When bucket list in snapshot is empty
class FailedToReadBucketDataFromSnapshot(DatabaseException):
    def __init__(self, message):
        super(FailedToReadBucketDataFromSnapshot, self).__init__(message)

# Command is not present in machine
class FailedToRunTheCommand(DatabaseException):
    def __init__(self, message):
        super(FailedToRunTheCommand, self).__init__(message)
