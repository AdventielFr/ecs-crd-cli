#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import json
import time
import traceback

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.destroyGreenStackStep import DestroyGreenStackStep
from ecs_crd.applyStrategyStep import CheckGreenHealthStep
from ecs_crd.destroyGreenStackStep import DestroyGreenStackStep
from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder

class ScaleUpServiceStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Scale Up Service', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            service_arn = self._find_service_arn()
            self.logger.info('')
            self._log_information(key='Service', value=self.infos.green_infos.stack_name)
            self._log_information(key='ARN', value=service_arn, indent=1)
            self.logger.info('')
            self.logger.info('Scaling up in progress ...')
            self.logger.info('')
            client = boto3.client('ecs', region_name=self.infos.region)
            if self.infos.scale_infos.desired > 1:
                client.update_service(
                    cluster=self.infos.cluster,
                    service=service_arn,
                    desiredCount=self.infos.scale_infos.desired,
                    deploymentConfiguration={
                        'maximumPercent': 100 * self.infos.scale_infos.desired,
                        'minimumHealthyPercent': 100
                    },
                    forceNewDeployment= True

                )
            else:
                client.update_service(
                    cluster=self.infos.cluster,
                    service=service_arn,
                    desiredCount=self.infos.scale_infos.desired,
                    forceNewDeployment= True)
            self._wait(self.infos.scale_infos.wait, 'Scaling up in progress')
            self.logger.info('')
            self.logger.info(f'Desired instances : {self.infos.scale_infos.desired}')
            return CheckGreenHealthStep(self.infos, self.logger)

        except Exception as e:
            self.logger.error('ScaleUpServiceStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 13
            return DestroyGreenStackStep(self.infos, self.logger)

    def _find_service_arn(self):
        """find AWS ARN of service"""
        client = boto3.client('cloudformation', region_name=self.infos.region)
        response = client.describe_stacks(StackName= self.infos.green_infos.stack_name)
        output = next(x for x in response['Stacks'][0]['Outputs'] if x['OutputKey']=='ServiceArn')
        return output['OutputValue']