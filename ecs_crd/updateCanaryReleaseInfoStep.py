#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import datetime

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.rollbackChangeRoute53WeightsStep import RollbackChangeRoute53WeightsStep
from ecs_crd.destroyBlueStackStep import DestroyBlueStackStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class UpdateCanaryReleaseInfoStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Update CanaryRelease Info (dynamo db)', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            client = boto3.resource('dynamodb', region_name=self.infos.region)
            table = client.Table('canary_release')
            if self.infos.action == 'deploy':
                if self._exist_item(client, table):
                    self._update_item(table)
                else:
                    self._insert_item(table)
            if self.infos.action == 'undeploy':
                self._delete_item(table)
            return DestroyBlueStackStep(self.infos, self.logger)
        except Exception as e:
            self.logger.error('UpdateCanaryReleaseInfoStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 4
            return RollbackChangeRoute53WeightsStep(self.infos, self.logger)

    def _exist_item(self, client, table):
        """check if exist item in dynamoDB table"""
        try:
            response = table.get_item(Key={'id': self.infos.get_hash()})
            return True if ('Item' in response and not response['Item']) else False
        except client.exceptions.ResourceNotFoundException:
            return False
        except Exception:
            raise

    def _delete_item(self, table):
        """delete item in dynamo db table """
        table.delete_item(Key={'id': self.infos.get_hash()})

    def _update_item(self, table):
        """update item in dynamo db table """
        table.update_item(
            Key={'id': self.infos.get_hash()},
            UpdateExpression="set service_version=:v, canary_releaset=:c, alb_arn=:a, deploy_at=:d, stack_name=:s",
            ExpressionAttributeValues={
                ':v': self.infos.service_version,
                ':c': self.infos.green_infos.stack['Parameters']['CanaryRelease']['Default'],
                ':a': self.infos.green_infos.stack['Parameters']['LoadBalancer']['Default'],
                ':d': str(datetime.datetime.now().replace(microsecond=0).isoformat()),
                ':s': self.infos.green_infos.stack_name
            },
            ReturnValues="UPDATED_NEW"
        )

    def _insert_item(self, table):
        """insert item in dynamo db table """
        item = {}
        item['id'] = self.infos.get_hash()
        item['canary_group'] = self.infos.canary_group
        item['service_name'] = self.infos.service_name
        item['service_version'] = self.infos.service_version
        item['environment'] = self.infos.environment
        item['project'] = self.infos.project
        item['region'] = self.infos.region
        item['canary_release'] = self.infos.green_infos.stack['Parameters']['CanaryRelease']['Default']
        item['alb_arn'] = self.infos.green_infos.stack['Parameters']['LoadBalancer']['Default']
        item['stack_name'] = self.infos.green_infos.stack_name
        item['deploy_at'] = str(datetime.datetime.now().replace(microsecond=0).isoformat())
        item['ecs_crd_version'] = self.infos.ecs_crd_version
        table.put_item(Item=item)