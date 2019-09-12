import boto3
import time
import json
import traceback

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.finishDeploymentStep import FinishDeploymentStep
from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder

class DestroyInitStackStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, 'Delete Init Cloudformation Stack', logger)
        self.timer  = 5
    
    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            if self.infos.init_infos.stack_id != None:
                client = boto3.client('cloudformation', region_name=self.infos.region)
                self._destroy_stack(client)
                self._monitor(client)
            else:
                self.logger.info('Not destruction stack (reason: the stack not exist).')
        except Exception as e:
            self.infos.exit_exception = e
            self.infos.exit_code = 8
            self.logger.error('DestroyGreenStackStep', exc_info=True)
        else:
            return FinishDeploymentStep(self.infos, self.logger)

    def _destroy_stack(self, client):
        """destroys the cloud formation stack"""
        client.delete_stack(StackName=self.infos.init_infos.stack_id)
    
    def _monitor(self, client):
        """pause the process and wait for the result of the cloud formation stack deletion"""
        wait = 0
        while True:
            wait = wait + self.timer
            w = self.second_to_string(wait)
            self.logger.info('')
            time.sleep(self.timer)
            self.logger.info(f'Deleting stack in progress ... [{w} elapsed]')
            response = client.describe_stacks(StackName = self.infos.init_infos.stack_id)
            stack = response['Stacks'][0]
            response2 = client.list_stack_resources(StackName = self.infos.init_infos.stack_id)
            for resource in response2['StackResourceSummaries']:
                message = resource['LogicalResourceId'].ljust(40,'.')+resource['ResourceStatus']
                if 'ResourceStatusReason'in resource:
                    message += f' ( {resource["ResourceStatusReason"]} )'
                self.logger.info(message)
                    
            if stack['StackStatus'] == 'DELETE_IN_PROGRESS':
                continue
            else:
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    break
                else:
                    raise ValueError('Error deletion green cloudformation stack')