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
        return SendNotificationBySnsStep(self.infos, self.logger)

    def _find_route_53_record_sets(self, client):
        result = {}
        hosted_zone_ids = list(set(list(map(lambda x: x.hosted_zone_id, self.infos.fqdn))))
        for hosted_zone_id in hosted_zone_ids:
            for k, v in self._find_route_53_record_sets_by_hosted_zone_id(client, hosted_zone_id).items():
                result[k] = v
        return result

    def _find_route_53_record_sets_by_hosted_zone_id(self, client, hosted_zone_id, start_record_name=None, start_record_type=None, start_record_identifier=None):
        result = {}
        client = boto3.client('route53')
        response = None
        if start_record_name:
            if start_record_identifier:
                response = client.list_resource_record_sets( 
                    HostedZoneId = hosted_zone_id, 
                    StartRecordName=start_record_name, 
                    StartRecordType=start_record_type, 
                    StartRecordIdentifier=start_record_identifier)
            else:
                response = client.list_resource_record_sets( 
                    HostedZoneId = hosted_zone_id, 
                    StartRecordName = start_record_name, 
                    StartRecordType = start_record_type)
        else:
            response = client.list_resource_record_sets( 
                HostedZoneId=hosted_zone_id)
        recordsets = response['ResourceRecordSets']
        for item in self.infos.fqdn:
            exist = list(filter(lambda x : x['Name'].strip('.') == item.name,  recordsets))
            if(len(exist)>0):
                result[item.name] = {}
                result[item.name]['ResourceRecordSets'] = exist
                result[item.name]['HostedZoneId'] = item.hosted_zone_id

        if 'IsTruncated' in response and bool(response['IsTruncated']):
            items = self._find_route_53_record_sets(client, hosted_zone_id, response['NextRecordName'], response['NextRecordType'], response['NextRecordIdentifier'] if 'NextRecordIdentifier' in response else None )
            for k, v in items:
                result[k] = v
        return result 

    def _clean_route_53_record_sets(self, client):
        """remove CNAME in route 53"""
        self.logger.info('Deleting Route53 records ... ')
        for k, v in self._find_route_53_record_sets(client).items():
            self.logger.info('')
            self._log_information(key='Fqdn', value=k)
            change_batch = {}
            change_batch['Comment'] = 'Remove Route53 records sets for canary blue-green deployment'
            change_batch['Changes'] = []
            for record in v['ResourceRecordSets']:
                change = {}
                change['Action'] = 'DELETE'
                change['ResourceRecordSet'] = record
                change_batch['Changes'].append(change)
            client.change_resource_record_sets(
                HostedZoneId=v['HostedZoneId'],
                ChangeBatch=change_batch
            )
        self.logger.info('')
        self.logger.info('Route53 records deleted with success.')
     