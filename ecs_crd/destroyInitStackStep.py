#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep
from ecs_crd.destroyStackStep import DestroyStackStep

class DestroyInitStackStep(DestroyStackStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos, 
            'Delete Init Cloudformation Stack', 
            logger,
            infos.init_infos
        )

    def _on_success(self):
        SendNotificationBySnsStep(self.infos, self.logger)
        
    def _on_fail(self):
        return None