#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

import logging

from controller import helper_lib

logger = logging.getLogger(__name__)

# This class is defined to capture vsdk parameters. So that to perform the operation, we don't need to pass the vsdk parameters
# again & again. Just create the object of this class and pass this across the operation. But for each different
# delphix operation initiated by plugin_runner.py, we need to create different instance for this class.
# If any parameter is not defined then it will be set as None.
#There is extra parameters(not coming from VSDK) also added -> dSource, source, parameters


class SchemaResource(object):
    def __init__(self,
                 source_connection=None,
                 repository=None,
                 source_config=None,
                 snapshot_parameters=None,
                 staged_source=None,
                 virtual_source=None,
                 snapshot=None,
                 dSource=True):
        """
        Defined in above of the class
        :param source_connection: Source connection object
        :param repository: instance of Repository class
        :param source_config: instance of SourceConfig
        :param snapshot_parameters: object of snapshot definition
        :param staged_source: object of staged source
        :param virtual_source: object of virtual source
        :param snapshot: snapshot object created at dsource time
        :param dSource: defines the dsource or vdb
        """

        self.source_connection = source_connection

        self.repository = repository

        self.source_config = source_config

        self.staged_source = staged_source

        self.snapshot_parameters = snapshot_parameters

        self.virtual_source = virtual_source

        self.snapshot = snapshot

        # Entry for other parameters which is being used in function

        if dSource is True:
            self.dSource = True
            self.connection = staged_source.staged_connection
            self.source = staged_source
        else:
            self.dSource = False
            self.connection = virtual_source.connection
            self.source = virtual_source

        self.parameters = self.source.parameters

        if(helper_lib.is_debug_enabled()):
            helper_lib.heading("        VSDK Parameters is listing here")
            logger.debug("source_connection- {}".format(self.source_connection))
            logger.debug("repository - {}".format(self.repository))
            logger.debug("source_config - \n{}".format(self.source_config))
            logger.debug("staged_source - \n {}".format(self.staged_source))
            logger.debug("snapshot_parameters - \n {}".format(self.snapshot_parameters))
            logger.debug("virtual_source - {}".format(self.virtual_source))
            logger.debug("snapshot - {}".format(self.snapshot))
            logger.debug("dSource - {}".format(self.dSource))
            logger.debug("source - {}".format(self.source))
            logger.debug("connection - {}".format(self.connection))
            helper_lib.heading("        END of list ")
            logger.debug("\n\n")
