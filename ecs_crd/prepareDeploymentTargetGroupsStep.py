#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentListenersStep import PrepareDeploymentListenersStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentTargetGroupsStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initialize a new instance of class"""
        super().__init__(infos, f'Prepare {infos.action} ( Target groups )', logger)

    def _process_target_group_tags(self, item, target_group):
        """update tags informations for the target group"""
        target_group['Properties']['Tags'] = []

        tag = {}
        tag['Key'] = "Environment"
        tag['Value'] = self.infos.environment
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Project"
        tag['Value'] = self.infos.project
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Service"
        tag['Value'] = self.infos.service_name
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Version"
        tag['Value'] = self.infos.service_version
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Container"
        tag['Value'] = item['ContainerName']
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "ContainerPort"
        tag['Value'] = str(item['ContainerPort'])
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "CanaryRelease"
        tag['Value'] = self.infos.green_infos.canary_release
        target_group['Properties']['Tags'].append(tag)

    def _process_target_group_port(self, item, target_group_info, target_group):
        """update port informations for the target group"""
        if 'port' in target_group_info:
            if isinstance(target_group_info['port'],int):
                target_group['Properties']['Port'] = int(
                    target_group_info['port'])
            else:
                if 'green' in target_group_info['port'] and 'blue' in target_group_info['port']:
                    target_group['Properties']['Port'] = int(
                        target_group_info['port'][self.infos.elected_release])
                else:
                    raise ValueError('Not found port target group informations for container {}:{} '.format(
                        item['ContainerName'], item['ContainerPort']))
        else:
            target_group['Properties']['Port'] = int(item['ContainerPort'])
        if target_group['Properties']['Port'] < 0:
            raise ValueError('{} is invalid for the port of target group'.format(
                target_group['Properties']['Port']))
        self._log_information(
            key='Port', value=target_group['Properties']['Port'], indent=1)

    def _process_target_group_protocol(self, item, target_group_info, target_group):
        """update protocol informations for the target group"""
        if 'protocol' in target_group_info:
            target_group['Properties']['Protocol'] = target_group_info['protocol'].upper()
        else:
            target_group['Properties']['Protocol'] = 'HTTP'
        if target_group['Properties']['Protocol'] not in ['HTTP', 'HTTPS']:
            raise ValueError('{} is not valid protocle'.format(
                target_group['Properties']['Protocol']))
        self._log_information(
            key='Procotol', value=target_group['Properties']['Protocol'], indent=1)

    def _process_target_group_attributes(self, item, target_group_info, target_group):
        """update attributes informations for the target group"""
        if 'target_group_attributes' in target_group_info:
            target_group['TargetGroupAttributes'] = []
            self._log_information(
                key='Target group attributes', value='', indent=1)
            for e in target_group_info['target_group_attributes']:
                target_group_attribute = {}
                target_group_attribute['Key'] = str(e['key'])
                target_group_attribute['Value'] = str(e['value'])
                target_group['TargetGroupAttributes'].append(
                    target_group_attribute)
                self._log_information(
                    key='- '+target_group_attribute['Key'], value=target_group_attribute['Value'], indent=2)

    def _process_target_group_health_check(self, item, target_group_info, target_group):
        """update health check informations for the target group"""
        if 'health_check' not in target_group_info:
            raise ValueError('health_check is mandatory.')
        target_group['Properties']['HealthCheckEnabled'] = "true"
        health_check_infos = target_group_info['health_check']
        self._log_information(key='Health Check', value='', indent=1)
        host_port = self._find_host_port(
            item['ContainerName'], item['ContainerPort'])
        if host_port != 0:
            # Port
            if 'port' in health_check_infos:
                if isinstance(health_check_infos['port'],int):
                    target_group['Properties']['HealthCheckPort'] = int(
                        health_check_infos['port'])
                else:
                    if 'green' in health_check_infos['port'] and 'blue' in health_check_infos['port']:
                        target_group['Properties']['HealthCheckPort'] = int(
                            health_check_infos['port'][self.infos.elected_release])
            self._log_information(
                key='Host port', value=target_group['Properties']['HealthCheckPort'], indent=2)
        else:
            self._log_information(key='Host port', value='dynamic', indent=2)
        # Interval seconds
        if 'interval_seconds' in health_check_infos:
            target_group['Properties']['HealthCheckIntervalSeconds'] = int(
                health_check_infos['interval_seconds'])
            self._log_information(
                key='Interval Seconds', value=target_group['Properties']['HealthCheckIntervalSeconds'], indent=2)

        # Healthy threshold count
        if 'healthy_threshold_count' in health_check_infos:
            target_group['Properties']['HealthyThresholdCount'] = int(
                health_check_infos['healthy_threshold_count'])
            self._log_information(key='Healthy Threshold Count',
                                  value=target_group['Properties']['HealthyThresholdCount'], indent=2)

        # Unhealthy threshold count
        if 'unhealthy_threshold_count' in health_check_infos:
            target_group['Properties']['UnhealthyThresholdCount'] = int(
                health_check_infos['unhealthy_threshold_count'])
            self._log_information(key='Unhealthy Threshold Count',
                                  value=target_group['Properties']['UnhealthyThresholdCount'], indent=2)

        # Path
        target_group['Properties']['HealthCheckPath'] = '/'
        if 'path' in health_check_infos:
            target_group['Properties']['HealthCheckPath'] = health_check_infos['path']

        self._log_information(
            key='Path', value=target_group['Properties']['HealthCheckPath'], indent=2)

        # Protocol
        if 'protocol' in health_check_infos:
            target_group['Properties']['HealthCheckProtocol'] = health_check_infos['protocol'].upper()
        else:
            target_group['Properties']['HealthCheckProtocol'] = 'HTTP'

        self._log_information(
            key='Protocol', value=target_group['Properties']['HealthCheckProtocol'], indent=2)

        # Matcher
        matcher = {}
        matcher['HttpCode'] = "200"
        if 'matcher' in health_check_infos:
            matcher['HttpCode'] = health_check_infos['matcher']

        target_group['Properties']['Matcher'] = matcher
        self._log_information(
            key='Matcher', value=matcher['HttpCode'], indent=2)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            cfn = self.infos.green_infos.stack['Resources']['Service']['Properties']['LoadBalancers']
            for item in cfn:

                target_group = {}
                target_group['Type'] = "AWS::ElasticLoadBalancingV2::TargetGroup"
                target_group['Properties'] = {}
                target_group['Properties']['Name'] = (
                    '{}-{}'.format(self.infos.id[:10], item['TargetGroupArn']['Ref'].replace('TargetGroup', '')[:18]))+'-tg'
                target_group['Properties']['VpcId'] = self.infos.vpc_id

                self._process_target_group_tags(item, target_group)

                target_group_info = None
                for elmt in self.configuration['target_groups']:
                    container_name = 'default'
                    if 'name' in elmt['container']:
                        container_name = elmt['container']['name']
                    if (elmt['container']['port'] == item['ContainerPort']
                            and container_name == item['ContainerName']):
                        target_group_info = elmt
                        break

                if target_group_info == None:
                    raise ValueError('Not found target group informations for container {}:{} '.format(
                        item['ContainerName'], item['ContainerPort']))

                container_name = 'default' if 'name' not in target_group_info[
                    'container'] else target_group_info['container']['name']
                self._log_sub_title('Container "{}:{}"'.format(
                    container_name, target_group_info['container']['port']))
                self._process_target_group_port(
                    item, target_group_info, target_group)
                self._process_target_group_protocol(
                    item, target_group_info, target_group)
                self._process_target_group_attributes(
                    item, target_group_info, target_group)
                self._process_target_group_health_check(
                    item, target_group_info, target_group)
                self.infos.green_infos.stack['Resources'][item['TargetGroupArn']
                                                          ['Ref']] = target_group

                # add result output
                self._add_to_output_cloud_formation(item['TargetGroupArn']['Ref'])

            self.infos.save()

            return PrepareDeploymentListenersStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 7
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)

    def _add_to_output_cloud_formation(self, target_group_name):
        output = self.infos.green_infos.stack['Outputs']
        id = target_group_name+'Arn'
        output[id] = {}
        output[id]['Description']=f'The ARN of {target_group_name}'
        output[id]['Value']={}
        output[id]['Value']['Ref'] = target_group_name

    def _find_host_port(self, container_name, container_port):
        """find the host port for tuple container name/ container port """
        cfn_container_definitions = self.infos.green_infos.stack['Resources'][
            'TaskDefinition']['Properties']['ContainerDefinitions']
        container_info = next(
            (x for x in cfn_container_definitions if x['Name'] == container_name), None)
        return next((x for x in container_info['PortMappings'] if x['ContainerPort'] == container_port), None)['HostPort']
