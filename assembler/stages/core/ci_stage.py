# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

import tempfile

from assembler.stages.core.ci import CloudInitUserData


class CIStage(object):
    NAME = 'CoreCI'
    DEPENDS = []

    def __init__(self, work_dir='.'):
        self._ci = CloudInitUserData()
        self._work_dir = work_dir
        self._has_run = False

    def run(self):
        if not self._has_run:
            print("Running %s stage" % (self.NAME))
            if self._ci.userdata_exists(self._work_dir) and self._ci.metadata_exists(self._work_dir):
                self._ci.load(self._work_dir)
            self._has_run = True
