import boto3
import json
import time
import traceback

from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.scaleUpServiceStep import ScaleUpServiceStep
from ecs_crd.finishDeploymentStep import FinishDeploymentStep

class CreateGreenStackStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, 'Create Green Cloudformation Stack', logger)
        self.timer  = 5
    
    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.logger.info('')
            self._log_information(key = 'Stack Name', value=self.infos.green_infos.stack_name)
            self.logger.info('')
            self.logger.info(f'Creating stack in progress ...')
            client = boto3.client('cloudformation', region_name = self.infos.region)
            self._create_stack(client)
            self._monitor(client)
            return ScaleUpServiceStep(self.infos, self.logger)
        except Exception as e:
            self.logger.error('CreateGreenStackStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 3
            return FinishDeploymentStep(self.infos, self.logger)

    
    def _monitor(self, client):
        """pause the process and wait for the result of the cloud formation stack creation"""
        wait = 0
        while True:
            wait = wait + self.timer
            w = self.second_to_string(wait)
            self.logger.info('')
            time.sleep(self.timer)
            self.logger.info(f'Creating stack in progress ... [{w} elapsed]')
            response = client.describe_stacks(StackName = self.infos.green_infos.stack_id)
            stack = response['Stacks'][0]
            response2 = client.list_stack_resources(StackName = self.infos.green_infos.stack_id)
            for resource in response2['StackResourceSummaries']:
                message = resource['LogicalResourceId'].ljust(40,'.')+resource['ResourceStatus']
                if 'ResourceStatusReason'in resource:
                    message += f' ( {resource["ResourceStatusReason"]} )'
                self.logger.info(message)
                    
            if stack['StackStatus'] == 'CREATE_IN_PROGRESS':
                continue
            else:
                if stack['StackStatus'] == 'CREATE_COMPLETE':
                    break
                else:
                    raise ValueError('Error creation green cloudformation stack')
   
    def _create_stack(self, client):
        """created the cloud formation stack"""
        payload = json.dumps(self.infos.green_infos.stack, cls=DefaultJSONEncoder)
        response = client.create_stack(
            StackName = self.infos.green_infos.stack_name,
            TemplateBody = payload,
            OnFailure='DELETE',
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=[
                {
                    'Key': 'Project',
                    'Value': self.infos.project
                },
                {
                    'Key': 'Service',
                    'Value': self.infos.service_name
                },
                {
                    'Key': 'Environment',
                    'Value': self.infos.environment
                },
                {
                    'Key': 'Version',
                    'Value': self.infos.service_version
                }]
            )
        self.infos.green_infos.stack_id = response['StackId']



