#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep
from ecs_crd.destroyInitStackStep import DestroyInitStackStep
from ecs_crd.destroyStackStep import DestroyStackStep

class DestroyBlueStackStep(DestroyStackStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos, 
            'Delete Blue Cloudformation Stack', 
            logger,
            infos.blue_infos
        )

    def _on_success(self):
        if self.infos.action == 'deploy':
            return SendNotificationBySnsStep(self.infos, self.logger)
        else:
            return DestroyInitStackStep(self.infos, self.logger)
        
    def _on_fail(self):
        return None
       
