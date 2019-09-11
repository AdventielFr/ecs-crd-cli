import click
import os
import logging
import boto3

from ecs_crd.prepareDeploymentGlobalParametersStep import PrepareDeploymentGlobalParametersStep
from ecs_crd.prepareUnDeploymentStep import PrepareUnDeploymentStep
from ecs_crd.canaryReleaseInfos import CanaryReleaseInfos

class Parameters:
    def __init__(self, logger):
        self.environments = ['dev', 'qua', 'stage', 'preprod', 'prod']
        self.regions = ['us-east-1','us-east-2','us-west-1','us-west-2','ap-east-1','ap-south-1','ap-northeast-1','ap-northeast-2','ap-northeast-3','ap-southeast-1','ap-southeast-2','ca-central-1','cn-north-1','cn-northwest-1','eu-central-1','eu-west-1','eu-west-2','eu-west-3','eu-north-1','sa-east-1','us-gov-east-1','us-gov-west-1']
        self.environment = None
        self.region = None
        self.configuration_file = None
        self.configuration_dir = None
        self.logger = logger

    def validate(self):
        if self.environment == None:
            raise ValueError(f'environment is mandatory.')
        if self.environment not in self.environments:
            raise ValueError(f'{self.environment} is not valid environment.')
        if self.region == None:
            raise ValueError(f'region is mandatory.')
        if self.region not in self.regions:
            raise ValueError(f'{self.region} is not valid aws region.')
    
        if self.configuration_file == None:
            if self.configuration_dir == None or self.configuration_dir == '':
                self.configuration_dir = os.getcwd()
            if not self.configuration_dir.endswith('/'):
                self.configuration_dir = self.configuration_dir+ '/'
            if not os.path.exists(self.configuration_dir):
                raise ValueError(f'{self.configuration_dir} not exist.')
            
            self.configuration_file = self.configuration_dir + self.environment + '.deploy.yml'
    
        if not os.path.isfile(self.configuration_file):
            raise ValueError(f'{self.configuration_file} not exist.')

        self.logger.info(''.ljust(50, '-'))
        self.logger.info(f'Step : Check parameters')
        self.logger.info(''.ljust(50, '-'))
        self.logger.info(f'Region             : {self.region}')
        self.logger.info(f'Environment        : {self.environment}')
        self.logger.info(f'Configuration      : {self.configuration_file}')
        self.logger.info('') 
        self.logger.info(f'Check parameters : COMPLETED')

@click.group()
def main():
    pass

@main.command()
@click.option('-e','--environment', required=True, default= 'stage', help='Environment to deploy.', show_default=True )
@click.option('-r','--region', required=True, default= 'eu-west-3', help='Amazon Web Service region used to deploy ECS service.', show_default=True )
@click.option('-f','--configuration-file', required=False, help='deployment configuration file.')
@click.option('-d','--configuration-dir', required=False, help='directory to find the deployment configuration file.')
@click.option('-v','--verbose', is_flag=True, default=False, help='activate verbose log.')
def deploy(
        environment, 
        region, 
        configuration_file,
        configuration_dir,
        verbose):
    logger, canary_infos = _common_action(environment, region, configuration_file, configuration_dir, verbose)
    canary_infos.action = 'deploy'
    canary_step = PrepareDeploymentGlobalParametersStep(canary_infos, logger)
    while (canary_step != None):
        canary_step = canary_step.execute()
    return canary_infos.exit_code

def _common_action(environment, region, configuration_file, configuration_dir, verbose):
    logger = _create_logger(verbose)
    parameters = Parameters(logger)
    parameters.environment = environment
    parameters.region = region
    parameters.configuration_file = configuration_file
    parameters.configuration_dir = configuration_dir
    parameters.validate()
    canary_infos = CanaryReleaseInfos(parameters.environment, parameters.region, parameters.configuration_file)
    return logger, canary_infos

@main.command()
@click.option('-e','--environment', required=True, default= 'stage', help='Environment to deploy.', show_default=True )
@click.option('-r','--region', required=True, default= 'eu-west-3', help='Amazon Web Service region used to deploy ECS service.', show_default=True )
@click.option('-c','--configuration-file', required=False, help='deployment configuration file.')
@click.option('-d','--configuration-dir', required=False, help='directory to find the deployment configuration file.')
@click.option('--verbose', count=True)
def un_deploy(
        environment, 
        region, 
        configuration_file,
        configuration_dir,
        verbose):
    logger, canary_infos = _common_action(environment, region, configuration_file, configuration_dir, verbose)
    canary_infos.action = 'undeploy'
    canary_step = PrepareUnDeploymentStep(canary_infos, logger)
    while (canary_step != None):
        canary_step = canary_step.execute()
    return canary_infos.exit_code

def _create_logger(verbose):
    logger = logging.getLogger('ecs-crd')
    logger.setLevel(logging.INFO)
    formatter = None
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger("boto3").setLevel(level)

    if level == logging.DEBUG:
        boto3.set_stream_logger(name='boto3', level=logging.DEBUG)
        boto3.set_stream_logger(name='botocore', level=logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s :  %(message)s')
    else:
        formatter= logging.Formatter('%(name)s : %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

if __name__ == '__main__':
    main()