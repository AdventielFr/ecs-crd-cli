#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3

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
        client = boto3.client('route53')
        self._clean_route_53_record_sets(client)
        return SendNotificationBySnsStep(self.infos, self.logger)
        
    def _on_fail(self):
        return None

    def _find_route_53_record_sets(self, client, start_record_name=None, start_record_type=None, start_record_identifier=None):
        dns = []
        client = boto3.client('route53')
        response = None
        if start_record_name:
            if start_record_identifier:
                response = client.list_resource_record_sets( 
                    HostedZoneId=self.infos.hosted_zone_id, 
                    StartRecordName=start_record_name, 
                    StartRecordType=start_record_type, 
                    StartRecordIdentifier=start_record_identifier)
            else:
                response = client.list_resource_record_sets( 
                    HostedZoneId=self.infos.hosted_zone_id, 
                    StartRecordName=start_record_name, 
                    StartRecordType=start_record_type)
        else:
            response = client.list_resource_record_sets( 
                HostedZoneId=self.infos.hosted_zone_id)
        result = response['ResourceRecordSets']
        dns += list(filter(lambda x: x['Name'].strip('.') == self.infos.fqdn, result))
        if 'IsTruncated' in response and bool(response['IsTruncated']):
            dns += self._find_route_53_record_sets(client, response['NextRecordName'], response['NextRecordType'], response['NextRecordIdentifier'] if 'NextRecordIdentifier' in response else None )
        return dns 

    def _clean_route_53_record_sets(self, client):
        """remove CNAME in route 53"""
        records = self._find_route_53_record_sets(client)
        if len(records) > 0:
            self.logger.info('Deleting Route53 records ... ')
            change_batch = {}
            change_batch['Comment'] = 'Remove Route53 records sets for canary blue-green deployment'
            change_batch['Changes'] = []
            for record in records:
                change = {}
                change['Action'] = 'DELETE'
                change['ResourceRecordSet'] = record
                change_batch['Changes'].append(change)
           
            client.change_resource_record_sets(
                HostedZoneId=self.infos.hosted_zone_id,
                ChangeBatch=change_batch
            )
            self.logger.info('Route53 records deleted with success.')
        else:
            self.logger.info('Not Route53 records to delete.')