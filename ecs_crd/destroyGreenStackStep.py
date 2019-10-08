#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep
from ecs_crd.destroyStackStep import DestroyStackStep

class DestroyGreenStackStep(DestroyStackStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos, 
            'Delete Green Cloudformation Stack', 
            logger,
            infos.green_infos
        )

    def _on_success(self):
        return SendNotificationBySnsStep(self.infos, self.logger)
        
    def _on_fail(self):
        return SendNotificationBySnsStep(self.infos, self.logger)