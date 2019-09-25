#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import urllib.request
import json

from ecs_crd.canaryReleaseInfos import ReleaseInfos
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.updateCanaryReleaseInfoStep import UpdateCanaryReleaseInfoStep


class PrepareUnDeploymentStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, 'Prepare undeployment', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        self.logger.info('')
        self.logger.info('Global infos :')
        self.logger.info(''.ljust(50, '-'))
        self.logger.info(f' Undeploy id    : {self.infos.id}')

        # account id
        self.infos.account_id = boto3.client('sts').get_caller_identity().get('Account')
        self.logger.info(f' Account id    : {self.infos.account_id}')

        # canary group
        self.infos.canary_group = self.configuration['canary']['group']
        self.logger.info(f' Canary group : {self.infos.canary_group}')

        # project
        self.infos.project = self.configuration['service']['project']
        self.logger.info(f' Project  : {self.infos.project}')
        self.infos.green_infos.stack['Parameters']['ProjectName']['Default'] = self.infos.project
        self.infos.init_infos.stack['Parameters']['ProjectName']['Default'] = self.infos.project

        # service name
        self.infos.service_name = self.bind_data(self.configuration['service']['name'])
        self.infos.green_infos.stack['Parameters']['ServiceName']['Default'] = self.infos.service_name
        self.infos.init_infos.stack['Parameters']['ServiceName']['Default'] = self.infos.service_name
        self.logger.info(f' Service  : {self.infos.service_name}')

        item = self._find_exist_dynamodb_item()
        self.infos.blue_infos = ReleaseInfos()
        if item:
            blue_stack = self._find_cloud_formation_stack(item['stack_name'])
            if blue_stack:
                self.infos.blue_infos.stack_id = blue_stack['StackId']
        self.logger.info(' Blue Stack : {}'.format(self.infos.blue_infos.stack_id))
        init_stack = self._find_cloud_formation_stack(f'{self.infos.environment}-{self.infos.service_name}-0')
        if init_stack:
            self.infos.init_infos = ReleaseInfos()
            self.infos.init_infos.stack_id = init_stack['StackId']
        self.logger.info(' Init Stack : {}'.format(self.infos.init_infos.stack_id))

        self.infos.save()

        return UpdateCanaryReleaseInfoStep(self.infos, self.logger)

    def _find_cloud_formation_stack(self, stack_name):
        client = boto3.client('cloudformation', region_name=self.infos.region)
        response = client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])
        count = sum(1 for e in response['StackSummaries'] if e['StackName'] == stack_name)
        if count == 0:
            return None
        response = client.describe_stacks(StackName=stack_name)
        if len(response['Stacks']) == 1:
            return response['Stacks'][0]
        else:
            return None

    def _find_exist_dynamodb_item(self):
        client = boto3.resource('dynamodb', region_name=self.infos.region)
        result = None
        try:
            table = client.Table('canary_release')
            response = table.get_item(Key={'id': self.infos.get_hash()})
            if 'Item' in response:
                result = response['Item']
        except client.exceptions.ResourceNotFoundException:
            pass
        except:
            raise
        return result