#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.createInitStackStep import CreateInitStackStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentInitStackStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Init stack )', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            for item in self.infos.fqdn:
                self.logger.info('')
                self._log_information(key='- Fqdn',value=item.name, indent=1)
                self._log_information(key='HostedZoneName',value=item.hosted_zone_name, indent=3)
                self._log_information(key='HostedZoneId',value=item.hosted_zone_id, indent=3)
            if self.infos.init_infos.stack:
                self._prepare_record_set_group()
            if self.infos.action == 'validate':
                return SendNotificationBySnsStep(self.infos,self.logger)
            else:
                return CreateInitStackStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 3
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)

    def _prepare_record_set_group(self):
        count = 1
        target = self.infos.init_infos.stack['Resources']
        for item in self.infos.fqdn:
            self._process_record_set_group_by_fqdn(item, count, target)
            count += 1
        self.infos.save()

    def _process_record_set_group_by_fqdn(self, source, count, target):
        """add RecordSetGroup by fqdn in cloudformation stack"""
        cfn = {}
        cfn['Type'] = 'AWS::Route53::RecordSetGroup'
        properties = {}
        properties['HostedZoneName'] = source.hosted_zone_name.strip('.')+'.'
        properties['RecordSets'] = []
        
        # blue 
        recordset = {}
        recordset['Name'] = source.name
        recordset['Type'] = 'CNAME'
        recordset['TTL'] = {}
        recordset['TTL']['Ref'] = 'Route53RecordetSetTTL'
        recordset['SetIdentifier'] = self.infos.blue_infos.canary_release
        recordset['Weight'] = 0
        recordset['ResourceRecords'] = []
        resource_record = {}
        resource_record['Ref'] = 'LoadBalancerBlue'
        recordset['ResourceRecords'].append(resource_record)
        properties['RecordSets'].append(recordset)

        # green 
        recordset = {}
        recordset['Name'] = source.name
        recordset['Type'] = 'CNAME'
        recordset['TTL'] = {}
        recordset['TTL']['Ref'] = 'Route53RecordetSetTTL'
        recordset['SetIdentifier'] = self.infos.green_infos.canary_release
        recordset['Weight'] = 100
        recordset['ResourceRecords'] = []
        resource_record = {}
        resource_record['Ref'] = 'LoadBalancerGreen'
        recordset['ResourceRecords'].append(resource_record)
        properties['RecordSets'].append(recordset)

        cfn['Properties'] = properties

        target[f'CanaryReleaseRecordSetGroup{count}'] = cfn