#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import json
import time
import traceback

from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.destroyGreenStackStep import DestroyGreenStackStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class RollbackChangeRoute53WeightsStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, 'Rollback Route53 Change DNS Weights', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            client = boto3.client('route53')
            if self.infos.blue_infos.stack_id !=None:
                if self._is_ready_to_rollback_weights(client):
                    self._rollback_weights(client)
                    self.wait(60, 'Change DNS Weights in progress')
            return DestroyGreenStackStep(self.infos, self.logger)
        except Exception as e:
            self.logger.error('RollbackChangeRoute53WeightsStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 7
            return SendNotificationBySnsStep(self.infos, self.logger)

    def _is_ready_to_rollback_weights(self, client):
        response = client.list_resource_record_sets(HostedZoneId=self.infos.hosted_zone_id)
        blue = list(filter(lambda x: x['Name'] == f"{self.infos.fqdn}." and x['SetIdentifier'] == self.infos.blue_infos.canary_release, response['ResourceRecordSets']))
        return int(blue[0]['Weight']) < 100

    def _rollback_weights(self, client):
        self.logger.info(f'FQDN : {self.infos.fqdn}')
        self.logger.info('Blue')
        self.logger.info(f' DNS     :{self.infos.blue_infos.alb_dns}')
        self.logger.info(f' Weight  :100%')
        self.logger.info(f' Release :{self.infos.blue_infos.canary_release}')
        self.logger.info('Green')
        self.logger.info(f' DNS     :{self.infos.green_infos.alb_dns}')
        self.logger.info(f' Weight  :0%')
        self.logger.info(f' Release :{self.infos.green_infos.canary_release}')     
        self.logger.info('')

        response = client.change_resource_record_sets(
            HostedZoneId=self.infos.hosted_zone_id,
            ChangeBatch={
                'Comment': 'Rollback Route53 records sets for canary blue-green deployment',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': self.infos.fqdn + '.',
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.blue_infos.canary_release,
                            'Weight': 100,
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.blue_infos.alb_dns
                                },
                            ]
                        }
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': self.infos.fqdn + '.',
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.green_infos.canary_release,
                            'Weight': 0,
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.green_infos.alb_dns
                                },
                            ]
                        }
                    }
                ]
            }
        )
