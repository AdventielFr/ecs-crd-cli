#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3

from ecs_crd.canaryReleaseInfos import ReleaseInfos
from ecs_crd.canaryReleaseInfos import LoadBalancerInfos
from ecs_crd.canaryReleaseInfos import ListenerRuleInfos
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentScaleParametersStep import PrepareDeploymentScaleParametersStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentLoadBalancerParametersStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Load Balancer parameters )', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            # récupération de l'item dynamo si il existe
            dynamodb_item = self._find_blue_dynamodb_item()

            # recherhcer de deux load balancers eligibles
            albs = self._find_load_balancers(dynamodb_item)

            # si le blue alb n'existe plus, on le supprime
            if dynamodb_item:
                if not any(filter(lambda x: x.arn == dynamodb_item['alb_arn'], albs)):
                    self._delete_obsolete_item()
                    dynamodb_item = None

            if len(albs) < 2:
                raise ValueError('There is not enough load balancer for a canary deployment.')
            elif len(albs) > 2:
                raise ValueError('There are too many load balancers for a canary deployment.')

            self.infos.init_infos.stack['Parameters']['LoadBalancerBlue']['Default'] = albs[0].dns_name
            self.infos.init_infos.stack['Parameters']['LoadBalancerGreen']['Default'] = albs[1].dns_name
            self.infos.init_infos.stack_name = self._generate_name(canary_release='0')

            exist = self._find_cloud_formation_stack(self.infos.init_infos.stack_name)

            if exist:
                 self.infos.init_infos.stack_id = exist['StackId']
                 self.infos.init_infos.stack = None

            # green infos
            greens = list(filter(lambda x: x.is_elected, albs))
            if not greens:
                raise ValueError(f'There is no ALB to deploy the Green release.')
            green = greens[0]

            self.infos.green_infos.stack['Parameters']['LoadBalancer']['Default'] = green.arn
            self.infos.green_infos.stack['Parameters']['CanaryRelease']['Default'] = green.canary_release
            self.infos.green_infos.alb_arn = green.arn
            self.infos.green_infos.canary_release = green.canary_release
            self.infos.green_infos.alb_dns = green.dns_name
            self.infos.green_infos.alb_hosted_zone_id = green.hosted_zone_id

            self.infos.green_infos.stack_name = self._generate_name(canary_release=green.canary_release)
            exist = self._find_cloud_formation_stack(self.infos.green_infos.stack_name)
            if exist:
                raise ValueError(f'There is already a cloudformation stack named for the Green release : {self.infos.green_infos.stack_name}.') 

            # blue infos
            blues = list(filter(lambda x: x != green, albs))
            blue = blues[0]
            self.infos.blue_infos = ReleaseInfos()
            self.infos.blue_infos.alb_arn = blue.arn
            self.infos.blue_infos.alb_dns = blue.dns_name
            self.infos.blue_infos.canary_release = blue.canary_release
            self.infos.blue_infos.alb_hosted_zone_id = green.hosted_zone_id
            if dynamodb_item:
                exist_blue_deployment = self._find_cloud_formation_stack(dynamodb_item['stack_name'])
                if exist_blue_deployment:
                    self.infos.blue_infos.stack_id = exist_blue_deployment['StackId']
                    self.infos.blue_infos.stack_name = f'{self.infos.environment}-{self.infos.service_name}-{blue.canary_release}'

            self._log_sub_title('Load balancer "blue" {}'.format('(elected)' if self.infos.elected_release == 'blue' and self.infos.action=='deploy' else ''))
            self._log_information(key='Fqdn', value=blue.dns_name, indent=1, ljust=4)
            self._log_information(key='ARN', value=blue.arn, indent=1, ljust=4)

            self._log_sub_title('Load balancer "green" {}'.format('(elected)' if self.infos.elected_release == 'green' and self.infos.action=='deploy' else ''))
            self._log_information(key='Fqdn', value=green.dns_name, indent=1, ljust=4)
            self._log_information(key='Dns', value=green.arn, indent=1, ljust=4)

            # init stack
            stack = self._find_cloud_formation_stack(self.infos.init_infos.stack_name)
            if stack and self.infos.action=='deploy':
                # no recreate init stack for deploy
                self.infos.init_infos.stack = None
            self.infos.save()
            return PrepareDeploymentScaleParametersStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 2
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)
         
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

    def _find_load_balancers(self, dynamodb_item):
        client = boto3.client('elbv2', region_name=self.infos.region)
        response = client.describe_load_balancers()
        albs = []
        for item in response['LoadBalancers']:
            if item['VpcId'] != self.infos.vpc_id or item['Type'] != 'application':
                continue
            arn = item['LoadBalancerArn']
            dnsName = item['DNSName']
            canonicalHostedZoneId = item['CanonicalHostedZoneId']
            canaryRelease = None
            canaryGroup = None
            # find tag informations
            response = client.describe_tags(ResourceArns=[arn])
            for tagDescriptions in response['TagDescriptions']:
                for tag in tagDescriptions['Tags']:
                    if tag['Key'] == 'CanaryRelease':
                        canaryRelease = tag['Value']
                    if tag['Key'] == 'CanaryGroup' and tag['Value'] == self.infos.canary_group:
                        canaryGroup = self.infos.canary_group

            # aln is ready 
            if canaryRelease and canaryGroup:
                albs.append(
                    LoadBalancerInfos(
                        arn=arn, 
                        dns_name= dnsName , 
                        canary_release = canaryRelease, 
                        hosted_zone_id=canonicalHostedZoneId
                    )
                )

        # no alb found to deploy
        if not albs:
            raise ValueError(f'There are no tagged ALBs ("{self.infos.environment}") allowing the service to be deployed.')

        blue_alb_arn = None
        if dynamodb_item:
            blue_alb_arn = dynamodb_item['alb_arn']

        elected_alb = None

        # rechecher de l'alb green
        for alb in albs:
            if alb.arn != blue_alb_arn:
                alb.is_elected = True
                elected_alb = alb
                response = client.describe_listeners(LoadBalancerArn=alb.arn)
                for item in self.configuration['listeners']:
                    # rechercher de l'écouteur associé au port 
                    listeners = list(filter(lambda x: x['Port'] == int(item['port']),response['Listeners']))
                    # le port est déjà écouté sur le 'load balancer' , on doit créer un 'listener rule'
                    if len(listeners) == 1:
                        listener = listeners[0]
                        # on vérifie qu'il y a une règle pour le
                        if 'rule' not in item:
                            container_name = 'default'
                            if 'container' in item['target_group'] and 'name' in item['target_group']['container']:
                                container_name = item['target_group']['container']['name']
                            raise ValueError('The listener port {} is already used for Alb:{}. You can either use a different port for the listener or set rules on the listener. ( ContainerName:{}, ContainerPort:{} )'.format(item['port'], alb.arn, container_name,  item['target_group']['container']['port'], ))
                        rule_infos = ListenerRuleInfos(listener_arn=listener['ListenerArn'], configuration=item)
                        self.infos.listener_rules_infos.append(rule_infos)
                break

        if not elected_alb:
            raise ValueError('Not Load balencer found for deploy.')
        self.infos.elected_release = 'blue' if str(elected_alb.canary_release) == str(self.configuration['canary']['releases']['blue']) else 'green'
        return albs

    def _delete_obsolete_item(self):
        client = boto3.resource('dynamodb', region_name=self.infos.region)
        table = client.Table('canary_release')
        table.delete_item(Key={'id': self.infos.get_hash()})

    def _find_blue_dynamodb_item(self):
        client = boto3.resource('dynamodb', region_name = self.infos.region)
        table = client.Table('canary_release')
        response = table.get_item(Key={'id': self.infos.get_hash()})

        if 'Item' in response:
            return response['Item']
        return None
