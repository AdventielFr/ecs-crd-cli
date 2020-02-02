#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3

from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep
from ecs_crd.destroyInitStackStep import DestroyInitStackStep
from ecs_crd.destroyStackStep import DestroyStackStep
from ecs_crd.canaryReleaseInfos import LoadBalancerInfos

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
        if self.infos.action == 'undeploy':
            #self._clean_route_53_record_sets()
            return DestroyInitStackStep(self.infos, self.logger)
        
    def _on_fail(self):
        return None
   
    def _clean_route_53_record_sets(self):
        """remove CNAME in route 53"""
        client = boto3.client('route53')
        client.change_resource_record_sets(
            HostedZoneId=self.infos.hosted_zone_id,
            ChangeBatch={
                'Comment': 'Remove Route53 records sets for canary blue-green deployment',
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': f"{self.infos.fqdn}.",
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.blue_infos.canary_release,
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.blue_infos.alb_dns
                                },
                            ]
                        },
                    },
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': f"{self.infos.fqdn}.",
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.green_infos.canary_release,
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.green_infos.alb_dns
                                },
                            ]
                        },
                    }
                ]
            }
        )
        
