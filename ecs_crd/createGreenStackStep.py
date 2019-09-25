#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import json
import time

from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder
from ecs_crd.createStackStep import CreateStackStep
from ecs_crd.scaleUpServiceStep import ScaleUpServiceStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep


class CreateGreenStackStep(CreateStackStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos, 
            'Create Green Cloudformation Stack', 
            logger,
            infos.green_infos)
        self.timer = 5

    def _on_success(self):
        return ScaleUpServiceStep(self.infos, self.logger)
        
    def _on_fail(self):
       return SendNotificationBySnsStep(self.infos, self.logger)
