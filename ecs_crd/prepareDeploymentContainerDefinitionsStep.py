#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.canaryReleaseInfos import SecretInfos
from ecs_crd.prepareDeploymentServiceDefinitionStep import PrepareDeploymentServiceDefinitionStep
from ecs_crd.updateCanaryReleaseInfoStep import UpdateCanaryReleaseInfoStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep


class PrepareDeploymentContainerDefinitionsStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(
            infos, f'Prepare {infos.action} ( Container definitions )', logger)

    def _process_container_name(self, source, target):
        """update the name informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='name',
            multi=True,
            parent_property='Service.Container',
            default='default',
            indent=1
        )

    def _process_container_image(self, source, target):
        """update the image informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='image',
            parent_property='Service.Container',
            default='{{account_id}}.dkr.ecr.{{region}}.amazonaws.com/{{name}}:{{version}}',
            indent=3
        )
        # check exist container image
        if self._is_container_image_from_ecr(source, target):
            if not self._exist_container_image_from_ecr(source, target):
                raise ValueError(
                    f'The container image {target["Image"]} is unknown in AWS ECR registry.')

    def _process_container_cpu(self, source, target):
        """update the cpu informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='cpu',
            parent_property='Service.Container',
            type=int,
            default=128,
            indent=3
        )

    def _process_container_memory(self, source, target):
        """update the cpu informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='memory',
            parent_property='Service.Container',
            type=int,
            default=128,
            indent=3
        )

    def _process_container_memory_reservation(self, source, target):
        """update the memory reservation informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='memory_reservation',
            parent_property='Service.Container',
            type=int,
            indent=3
        )

    def _process_container_port_mappings(self, source, target):
        """update the port mappings informations for the current container"""
        if 'port_mappings' in source:
            target['PortMappings'] = []
            self._log_information(key='Port mappings', value='', indent=3)
            for p in source['port_mappings']:
                port_mapping = {
                    'HostPort': 0,
                    'ContainerPort': int(p['container_port'])
                }
                if 'host_port' in p:
                    if isinstance(p['host_port'], int):
                        port_mapping['HostPort'] = p['host_port']
                    elif 'green' in p['host_port'] and 'blue' in p['host_port']:
                        port_mapping['HostPort'] = int(
                            p['host_port'][self.infos.elected_release])
                protocol = 'tcp'
                host_port = ''
                if port_mapping['HostPort'] == 0:
                    host_port = '"dynamic"'
                else:
                    host_port = '{} ({})'.format(
                        port_mapping['HostPort'], self.infos.elected_release)
                if 'protocol' in p:
                    protocol = p['protocol']
                    port_mapping['Protocol'] = protocol
                target['PortMappings'].append(port_mapping)
                self._log_information(key='- '+protocol, value='{} -> {}'.format(
                    host_port, port_mapping['ContainerPort']), indent=4)

    def _process_container_entry_point(self, source, target):
        """update the entry point informations for the current container"""
        if 'entry_point' in source:
            if isinstance(source['entry_point'], list):
                target['EntryPoint'] = ','.join(source['entry_point'])
                self._log_information(
                    key='Entry point', value=target["EntryPoint"], indent=3)
            else:
                raise ValueError(
                    f'{source["entry_point"]} is not valid EntryPoint for Container.')

    def _process_container_environment(self, source, target):
        """update the environment informations for the current container"""
        target['Environment'] = []
        if 'environment' in source:
            for elmt in source['environment']:
                e = {}
                for k, v in elmt.items():
                    e['Name'] = k
                    e['Value'] = v
                e['Value'] = self._bind_data(str(v))
                target['Environment'].append(e)
        # ajout variable d'environement par défault
        self._add_default_environment_variable(
            target, 'AWS_ENVIRONMENT', '{{environment}}')
        self._add_default_environment_variable(
            target, 'AWS_REGION', '{{region}}')
        self._add_default_environment_variable(
            target, 'AWS_ACCOUNT_ID', '{{account_id}}')
        self._log_information(key='Environment', value='', indent=3)
        for e in target['Environment']:
            self._log_information(
                key=e['Name'], value=e['Value'], indent=4)

    def _process_container_secrets(self, source, target):
        """update the secrets informations for the current container"""
        target['Secrets'] = []
        if 'secrets' in source:
            self._log_information(key='Secrets', value='', indent=3)
            for elmt in source['secrets']:
                # TODO A retravailler
                e = {}
                for a in elmt.keys():
                    e['Name'] = a
                e['ValueFrom'] = None
                for a in elmt.values():
                    e['ValueFrom'] = a
                    e['ValueFrom'] = self._bind_data(e['ValueFrom'])
                for s in self.infos.secret_infos.secrets:
                    if s['id'] == e['ValueFrom']:
                        e['ValueFrom'] = s['arn']
                target['Secrets'].append(e)
                self._log_information(
                    key=e['Name'], value=e['ValueFrom'], indent=4)

    def _process_container_command(self, source, target):
        """update the command informations for the current container"""
        if 'command' in source:
            if isinstance(source['command'], list):
                self._log_information(key='Command', value='', indent=3)
                target['Command'] = []
                for e in source['command']:
                    target['Command'].append(e)
                    self._log_information(key='- '+e, value=None, indent=5)
            else:
                raise ValueError(
                    f'{source["command"]} is not valid Command for Container.')

    def _process_container_dns_search_domains(self, source, target):
        """update the dns search domain informations for the current container"""
        if 'dns_search_domains' in source:
            if isinstance(source['dns_search_domains'], list):
                self._log_information(
                    key='Dns Search Domains', value='', indent=3)
                target['DnsSearchDomains'] = []
                for e in source['dns_search_domains']:
                    target['DnsSearchDomains'].append(e)
                    self._log_information(key='- '+e, value=None, indent=5)
            else:
                raise ValueError(
                    f'{source["dns_search_domains"]} is not valid DnsSearchDomains for Container.')

    def _process_container_disable_networking(self, source, target):
        """update the disable networking informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='disable_networking',
            parent_property='Container',
            type=bool,
            indent=3
        )

    def _process_container_dns_servers(self, source, target):
        """update the dns servers informations for the current container"""
        if 'dns_servers' in source:
            if isinstance(source['dns_servers'], list):
                self._log_information(key='Dns Servers', value='', indent=1)
                target['DnsServers'] = []
                for e in source['dns_servers']:
                    target['DnsServers'].append(e)
                    self._log_information(key='- '+e, value=None, indent=2)
            else:
                raise ValueError(
                    f'{source["dns_servers"]} is not valid DnsServers for Container.')

    def _process_container_links(self, item, container):
        """update the links informations for the current container"""
        if 'links' in item:
            self._log_information(key='Links', value='', indent=1)
            container['Links'] = []
            for e in item['links']:
                container['Links'].append(e)
                self._log_information(key='- '+e, value=None, indent=2)

    def _process_container_docker_security_options(self, item, container):
        """update the docker security informations for the current container"""
        if 'docker_security_options' in item:
            self._log_information(
                key='Docker Security Options', value='', ljust=10, indent=1)
            container['DockerSecurityOptions'] = []
            for e in item['docker_security_options']:
                container['DockerSecurityOptions'].append(e)
                self._log_information(key='- '+e, value=None, indent=2)

    def _process_container_essential(self, item, container):
        """update the essential informations for the current container"""
        container["Essential"] = "true"
        if 'essential' in item:
            if str(item['essential']).lower().strip() == 'true':
                container['Essential'] = "true"
            else:
                container['Essential'] = "false"
        self._log_information(
            key='Essential', value=container["Essential"], indent=3)

    def _is_container_image_from_ecr(self, item, container):
        return container['Image'].startswith(self._bind_data('{{account_id}}.dkr.ecr.{{region}}.amazonaws.com/'))

    def _exist_container_image_from_ecr(self, item, container):
        client = boto3.client('ecr', region_name=self.infos.region)
        try:
            data = container['Image'].split('/')
            registry = data[0]
            data = data[1].split(':')
            repository = data[0]
            tag = data[1]
            response = client.describe_images(
                repositoryName=repository, imageIds=[{"imageTag": tag}])
            return len(response["imageDetails"]) == 1
        except Exception as e:
            self.logger.error(e)
            return False

    def _process_container_privileged(self, item, container):
        """update the privileged informations for the current container"""
        if 'privileged' in item:
            if str(item['privileged']).lower().strip() == 'true':
                container['Privileged'] = "true"
            else:
                container['Privileged'] = "false"
            self._log_information(
                key='Priviliged', value=container["Privileged"], indent=1)
    
    def _process_container_healthcheck(self, item, container):
        """update the healthcheck informations for the current container"""
        if 'health_check' in item:
            self._log_information(key='HealthCheck', value='', indent=2)
            health_check = {}
            health_check['Command'] = []
            self._log_information(
                key='Command', value='', indent=3)
            for command in item['health_check']['command']:
                health_check['Command'].append(command)
                self._log_information(
                    key= '- ' +command, value=None, indent=4)                
            if 'interval' in item['health_check']:
                health_check['Interval'] = int(item['health_check']['interval'])
                self._log_information(
                    key='Interval', value=mount_point["Interval"], indent=2)
            if 'retries' in item['health_check']:
                health_check['Retries'] = int(item['health_check']['retries'])    
                self._log_information(
                    key='Retries', value=health_check["Retries"], indent=2)
            if 'start_period' in item['health_check']:
                health_check['StartPeriod'] = int(item['health_check']['start_period'])
                self._log_information(
                    key='StartPeriod', value=health_check["StartPeriod"], indent=2)
            if 'timeout' in item['health_check']:
                health_check['Timeout'] = int(item['health_check']['timeout'])   
                self._log_information(
                    key='Timeout', value=health_check["Timeout"], indent=2)         
            container['HealthCheck'] = health_check

    def _process_container_mount_points(self, item, container):
        """update the mount points informations for the current container"""
        if 'mount_points' in item:
            self._log_information(key='Mount points', value='', indent=1)
            container['MountPoints'] = []
            for e in item['mount_points']:
                mount_point = {}
                mount_point['ContainerPath'] = self._bind_data(
                    e['container_path'])
                self._log_information(
                    key='- Container Path', value=mount_point["ContainerPath"], indent=2)
                mount_point['SourceVolume'] = self._bind_data(
                    e['source_volume'])
                self._log_information(
                    key='  Source Volume', value=mount_point["SourceVolume"], indent=2)
                mount_point['ReadOnly'] = "false"
                if 'read_only' in e:
                    if str(e['read_only']).lower().strip() == 'true':
                        mount_point['ReadOnly'] = "true"
                    else:
                        mount_point['ReadOnly'] = "false"
                    self._log_information(
                        key='  Read Only', value=mount_point["ReadOnly"], indent=2)
                container['MountPoints'].append(mount_point)

    def _process_container_hostname(self, source, target):
        """update the hostname informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='hostname',
            parent_property='Container',
            indent=3
        )

    def _process_container_start_timeout(self, source, target):
        """update the start timeout informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='start_timeout',
            parent_property='Container',
            type=int,
            indent=3
        )

    def _process_container_stop_timeout(self, source, target):
        """update the stop timeout informations for the current container"""
        self._process_property(
            source=source,
            target=target,
            source_property='stop_timeout',
            parent_property='Container',
            type=int,
            indent=3
        )

    def _process_container_log_configuration(self, item, container):
        container['LogConfiguration'] = {}
        if 'log_configuration' in item:
            log_configuration = item['log_configuration']
            container['LogConfiguration']['LogDriver'] = log_configuration['log_driver']
            if 'options' in log_configuration:
                container['LogConfiguration']['Options'] = {}
                e = {}
                for k, v in log_configuration['options'].items():
                    e['Name'] = k
                    e['Value'] = self._bind_data(str(v))
                    container['LogConfiguration']['Options'].append(e)
            if 'secret_options' in log_configuration:
                container['LogConfiguration']['SecretOptions'] = {}
                for i in log_configuration['secret_options']:
                    e = {}
                    e['Name'] = i['name']
                    e['ValueFrom'] = self._bind_data(i['value_from'])
                    container['LogConfiguration']['SecretOptions'].append(e)                 

        else:
            container['LogConfiguration'] = {}
            container['LogConfiguration']['LogDriver'] = 'awslogs'
            container['LogConfiguration']['Options'] = {}
            container['LogConfiguration']['Options'][
                'awslogs-group'] = f'/aws/ecs/{self.infos.cluster_name}/service/{self.infos.service_name}'
            container['LogConfiguration']['Options']['awslogs-region'] = self.infos.region
            container['LogConfiguration']['Options']['awslogs-stream-prefix'] = self.infos.service_version

        self._log_information(key='Log Configuration', value='', indent=3)
        self._log_information(
            key='Log Driver', value = container['LogConfiguration']['LogDriver'], indent=4)
        self._log_information(key='Options', value='', indent=4)
        for k,v in container['LogConfiguration']['Options'].items():
            self._log_information(
                key='- Name', value= k, indent=5)
            self._log_information(
                key='  Value', value= v, indent=5)
        if 'SecretOptions' in container['LogConfiguration']:
            self._log_information(key='SecretOptions', value='', indent=4)
            for k, v in container['LogConfiguration']['SecretOptions'].items():
                self._log_information(
                    key='- Name', value=k, indent=5)
                self._log_information(
                    key='  ValueFrom', value=v, indent=5)                

    def _process_container_depends_on(self, item, container):
        """update the depends on for the current container"""
        if 'depends_on' in item:
            container['DependsOn'] = []
            self._log_information(key='Depend On', value='', indent=4)
            for i in item['depends_on']:
                depends_on = {}
                depends_on['Condition'] = i['condition']
                depends_on['ContainerName'] = i['container_name']
                container['DependsOn'].append(depends_on)
                self._log_information(
                    key='- ContainerName', value=depends_on['ContainerName'], indent=5)
                self._log_information(
                    key='  Condition', value=depends_on['Condition'], indent=5)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.infos.secret_infos = self._find_secrets_task_informations()
            cfn = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['ContainerDefinitions']
            for source in self.configuration['service']['containers']:
                target = {}
                self._process_container_name(source, target)
                self._process_container_image(source, target)
                self._process_container_cpu(source, target)
                self._process_container_memory(source, target)
                self._process_container_memory_reservation(source, target)
                self._process_container_port_mappings(source, target)
                self._process_container_entry_point(source, target)
                self._process_container_environment(source, target)
                self._process_container_secrets(source, target)
                self._process_container_command(source, target)
                self._process_container_dns_search_domains(source, target)
                self._process_container_disable_networking(source, target)
                self._process_container_dns_servers(source, target)
                self._process_container_docker_security_options(source, target)
                self._process_container_essential(source, target)
                self._process_container_links(source, target)
                self._process_container_privileged(source, target)
                self._process_container_mount_points(source, target)
                self._process_container_hostname(source, target)
                self._process_container_log_configuration(source, target)
                self._process_container_start_timeout(source, target)
                self._process_container_stop_timeout(source, target)
                self._process_container_depends_on(source, target)
                self._process_container_healthcheck(source, target)

                cfn.append(target)
            self.infos.save()
            if self.infos.action == 'undeploy':
                return UpdateCanaryReleaseInfoStep(self.infos, self.logger)
            else:
                return PrepareDeploymentServiceDefinitionStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 4
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)

    def _add_default_environment_variable(self, target, key, value):
        """add a new default environment variables if not exists"""
        if not any(filter(lambda x: x['Name'] == key, target['Environment'])):
            env = {}
            env['Name'] = key
            env['Value'] = self._bind_data(value)
            target['Environment'].append(env)

    def _find_secrets_task_informations(self):
        """find secret task information for vault resolution in excution task role."""
        result = None
        o = []

        for container_infos in self.configuration['service']['containers']:
            if 'secrets' in container_infos:
                for item in container_infos['secrets']:
                    format = self._bind_data(str(item)).replace('\'', '"')
                    j = json.loads(format)
                    o.append(j)
        # no secrets
        if not o:
            return None
        # secrets exist
        result = SecretInfos()
        client = boto3.client('secretsmanager', region_name=self.infos.region)
        kmsKeyIds = []
        for item in o:
            for k, v in item.items():
                secretId = v
                try:
                    response = client.describe_secret(SecretId=secretId)
                    if response['ARN'] not in result.secrets_arn:
                        a = {}
                        a['id'] = v
                        a['arn'] = response['ARN']
                        result.secrets.append(a)
                        result.secrets_arn.append(response['ARN'])
                        if response['KmsKeyId'] not in kmsKeyIds:
                            kmsKeyIds.append(response['KmsKeyId'])
                except Exception as e:
                    raise ValueError(f'Invalid secret: {secretId}, reason:{e}')

        client = boto3.client('kms',  region_name=self.infos.region)
        for k in kmsKeyIds:
            response = client.describe_key(
                KeyId=k, GrantTokens=['DescribeKey'])
            result.kms_arn.append(response['KeyMetadata']['Arn'])
        return result
