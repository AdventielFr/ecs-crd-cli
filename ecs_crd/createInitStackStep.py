#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3

from ecs_crd.createStackStep import CreateStackStep
from ecs_crd.createGreenStackStep import CreateGreenStackStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class CreateInitStackStep(CreateStackStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos,
            'Create Init Cloudformation Stack', 
            logger,
            infos.init_infos)
        #if self.infos.init_infos.stack: 
  
    def _on_success(self):
        return CreateGreenStackStep(self.infos, self.logger)
        
    def _on_fail(self):
       return SendNotificationBySnsStep(self.infos, self.logger)
