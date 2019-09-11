import boto3
import urllib.request
import json

from ecs_crd.canaryReleaseInfos import StrategyInfos
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentScaleParametersStep import PrepareDeploymentScaleParametersStep

class PrepareDeploymentGlobalParametersStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Global parameters )', logger)

    def _process_account_id(self):
        """update the AWS account ID informations for the service"""
        self.infos.account_id = boto3.client('sts').get_caller_identity().get('Account')
        self.logger.info(f' Account id    : {self.infos.account_id}')

    def _process_canary_group(self):
        """update the canary group name informations for the service"""
        self.infos.canary_group = self.configuration['canary']['group']
        self.logger.info(f' Canary group : {self.infos.canary_group}')

    def _process_external_ip(self):
        """update the external ip informations for the service"""
        self.infos.external_ip = self._find_external_ip()
        self.logger.info(f' External IP  : {self.infos.external_ip}')

    def _process_project(self):
        """update the project name informations for the service"""
        self.infos.project = self.configuration['service']['project']
        self.logger.info(f' Project  : {self.infos.project}')
        self.infos.green_infos.stack['Parameters']['ProjectName']['Default'] = self.infos.project
        self.infos.init_infos.stack['Parameters']['ProjectName']['Default'] = self.infos.project

    def _process_service_name(self):
        """update the name informations for the service"""
        self.infos.service_name = self.bind_data(self.configuration['service']['name'])
        self.infos.green_infos.stack['Parameters']['ServiceName']['Default'] = self.infos.service_name
        self.infos.init_infos.stack['Parameters']['ServiceName']['Default'] = self.infos.service_name
        self.logger.info(f' Service  : {self.infos.service_name}')
    
    def _process_version(self):
        """update the version informations for the service"""
        version = 'latest'
        if 'version' in self.configuration['service']:
            version = str(self.configuration['service']['version'])
        self.infos.service_version = version
        self.infos.green_infos.stack['Parameters']['Version']['Default'] = self.infos.service_version
        self.logger.info(f' Version  : {self.infos.service_version}')

    def _process_fqdn(self):
        """update the fqdn informations for the service"""
        fqdn = self.bind_data(self.configuration['service']['fqdn'])
        self.infos.fqdn = fqdn
        self.logger.info(f' Fqdn : {self.infos.fqdn}')
        self.infos.init_infos.stack['Parameters']['Fqdn']['Default'] = fqdn

    def _process_hosted_zone_name(self):
        """update the AWS route53 hosted zone informations for the service"""
        data = self.infos.fqdn.split('.')
        hostZoneName = data[len(data)-2] + '.' + data[len(data)-1] + '.'
        self.infos.init_infos.stack['Parameters']['HostedZoneName']['Default'] = hostZoneName
        self.logger.info(f' Dns zone : {hostZoneName}')
        hostedZone = self._find_hosted_zone(hostZoneName)
        if hostedZone == None:
            raise ValueError(f'HostedZone {hostZoneName} not found, create Route53 Zone before deploy')
        self.infos.hosted_zone_id = hostedZone['Id'].split('/')[2]

    def _process_vpc_id(self):
        """update the AWS vpc ID informations for the service"""
        self.infos.vpc_id = self._find_vpc_Id()
    
    def _process_cluster(self):
        """update the AWS ECS cluster informations for the service"""
        # clusterName 
        clusterName = self.bind_data('{{environment}}-ecs-cluster')
        if 'cluster' in self.configuration['service']:
            clusterName = self.bind_data(self.configuration['service']['cluster'])
        self.infos.cluster_name = clusterName
        self.logger.info(f' Cluster  : {self.infos.cluster_name}')
        self.infos.green_infos.stack['Parameters']['ClusterName']['Default'] = clusterName
        self.infos.init_infos.stack['Parameters']['ClusterName']['Default'] = clusterName

        # cluster
        cluster = self._find_cluster(clusterName)
        self.infos.cluster = cluster
        self.infos.green_infos.stack['Parameters']['Cluster']['Default'] = cluster

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
        
            self.logger.info('')
            self.logger.info('Global infos :')
            self.logger.info(''.ljust(50, '-'))
            self.logger.info(f' Deploy id    : {self.infos.id}')
        
            self._process_account_id()
            self._process_canary_group()
            self._process_external_ip()
            self._process_project()
            self._process_service_name()
            self._process_version()
            self._process_fqdn()
            self._process_hosted_zone_name()
            self._process_vpc_id()
            self._process_cluster()
            self.infos.save()
            self._create_dynamodb_table()

            return PrepareDeploymentScaleParametersStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def _find_vpc_Id(self):
        """find the AWS VPC by environment"""
        ec2 = boto3.resource('ec2', region_name = self.infos.region)
        client = boto3.client('ec2', region_name = self.infos.region)
        ids = map(lambda x: x.id, list(ec2.vpcs.filter(Filters=[])))
        for id in ids:
            response = client.describe_vpcs(VpcIds=[id])
            if 'Tags' in response['Vpcs'][0]:
                for tag in response['Vpcs'][0]['Tags']:
                    if tag['Key'] == 'Environment' and tag['Value'] == self.infos.environment:
                        return id
        raise ValueError('vpc id {} not found for environment'.format(self.infos.environment))

    def _find_cluster(self, clusterName):
        """find the AWS ECS cluster by name"""
        client = boto3.client('ecs', region_name = self.infos.region)
        response = client.list_clusters()
        for arn in response['clusterArns']:
            if arn.endswith(clusterName):
                return arn
        raise ValueError(f'Cluster "{clusterName}" not found.')

    
    def _find_hosted_zone(self, hostZoneName):
        """find the AWS Route53 dns zone by name"""
        client = boto3.client('route53', region_name = self.infos.region)
        response = client.list_hosted_zones()
        for item in response['HostedZones']:
            if item['Name'] == hostZoneName:
                return item

    def _create_dynamodb_table(self):
        """create the AWS DynamoDB table if not exist"""
        client = boto3.client('dynamodb', region_name = self.infos.region)
        table_name = 'canary_release'
        existing_tables = client.list_tables()['TableNames']
        if table_name not in existing_tables:
            client.create_table(
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S',
                    },
                ],
                KeySchema=[
                    {
                        'AttributeName':'id',
                        'KeyType': 'HASH',
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2,
                },
                TableName='canary_release',
            )
    
    def _find_external_ip(self):
        """find the external ip"""
        try:
            data = json.loads(urllib.request.urlopen("http://ip.jsontest.com/").read())
            return data['ip']
        except:
            return None
