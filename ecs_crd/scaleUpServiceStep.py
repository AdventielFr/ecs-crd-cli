import boto3
import json
import time
import traceback

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.destroyGreenStackStep import DestroyGreenStackStep
from ecs_crd.applyStrategyStep import ChangeRoute53WeightsStep
from ecs_crd.destroyGreenStackStep import DestroyGreenStackStep
from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder

class ScaleUpServiceStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Scale Up Service', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.logger.info('')
            self.logger.info('Scaling up service in progress ...')
            self.logger.info('')
            time.sleep(10)
            client = boto3.client('ecs', region_name=self.infos.region)
            service_arn = self._find_service_arn(client)
            self.logger.info(f'Service : {service_arn}')
            if service_arn == None:
                raise ValueError(f'Service not found')
            self.logger.info('')
            client.update_service(
                cluster = self.infos.cluster,
                service = service_arn,
                desiredCount = self.infos.scale_infos.desired,
                deploymentConfiguration={
                    'maximumPercent': 100 * self.infos.scale_infos.desired,
                    'minimumHealthyPercent': 100
                }
            )
            self.wait(self.infos.scale_infos.wait, 'Scaling up in progress')
            self.logger.info('')
            self.logger.info(f'Desired instances : {self.infos.scale_infos.desired}')
            return ChangeRoute53WeightsStep(self.infos, self.logger)

        except Exception as e:
            self.logger.error('ScaleUpServiceStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 4
            return DestroyGreenStackStep(self.infos, self.logger)

    def _find_service_arn(self, client):
        """find AWS ARN of service"""
        response = client.list_services(cluster=self.infos.cluster)
        for item in response['serviceArns']:
            s = []
            s.append(item)
            response = client.describe_services( cluster = self.infos.cluster, services=s)
            if response['services'][0]['serviceName'] == '-'.join([self.infos.service_name, self.infos.green_infos.canary_release]):
                return response['services'][0]['serviceArn']