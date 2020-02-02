#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import time
import uuid
import datetime

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep

class FinishDeploymentStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Finish {infos.action}', logger, with_end_log=False)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        if self.infos.exit_code == 0:
            self.logger.info('Result      : COMPLETED')
        else:
            self.logger.info('Result      : FAILED')
            self.logger.info(f'Exit code   : {self.infos.exit_code}')
            self.logger.info(f'Exit error  : {self.infos.exit_exception}')
        return None
