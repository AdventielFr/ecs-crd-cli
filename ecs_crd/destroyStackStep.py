#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import time
from abc import ABC, abstractmethod

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep

class DestroyStackStep(CanaryReleaseDeployStep):

    def __init__(self, infos, title, logger, stack_infos ):
        """initializes a new instance of the class"""
        super().__init__(
            infos, 
            title, 
            logger
        )
        self.timer = 5
        self.stack_infos = stack_infos

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            if self.stack_infos.stack_id:
                client = boto3.client('cloudformation', region_name=self.infos.region)
                self._destroy_stack(client)
                self._monitor(client)
            else:
                self.logger.info('Not destruction stack (reason: the stack not exist).')
            self.stack_infos.stack_id = None   
            self.infos.save()
            return self._on_success()
        except Exception as e:
            self.infos.exit_exception = e
            self.infos.exit_code = 17
            self.logger.error(self.title, exc_info=True)
            return self._on_fail()
   
    @abstractmethod
    def _on_success(self):
        pass
        
    @abstractmethod
    def _on_fail(self):
        pass

    def _destroy_stack(self, client):
        """destroys the cloud formation stack"""
        client.delete_stack(StackName=self.stack_infos.stack_id)

    def _monitor(self, client):
        """pause the process and wait for the result of the cloud formation stack deletion"""
        wait = 0
        while True:
            wait += self.timer
            w = self._second_to_string(wait)
            self.logger.info('')
            time.sleep(self.timer)
            self.logger.info(f'Deleting stack in progress ... [{w} elapsed]')
            response = client.describe_stacks(StackName=self.stack_infos.stack_id)
            stack = response['Stacks'][0]
            response2 = client.list_stack_resources(StackName=self.stack_infos.stack_id)
            for resource in response2['StackResourceSummaries']:
                message = resource['LogicalResourceId'].ljust(40, '.') + resource['ResourceStatus']
                if 'ResourceStatusReason' in resource:
                    message += f' ( {resource["ResourceStatusReason"]} )'
                self.logger.info(message)

            if stack['StackStatus'] == 'DELETE_IN_PROGRESS':
                continue
            else:
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    break
                else:
                    raise ValueError('Error deletion cloudformation stack')