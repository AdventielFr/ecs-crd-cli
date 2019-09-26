import json
import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.canaryReleaseInfos import SecretInfos
from ecs_crd.prepareDeploymentServiceDefinitionStep import PrepareDeploymentServiceDefinitionStep


class PrepareDeploymentContainerDefinitionsStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Container definitions )', logger)

    def _process_container_name(self, item, container):
        """update the name informations for the current container"""
        container['Name'] = 'default'
        if 'name' in item:
            container['Name'] = item['name']
        self._log_sub_title('Container "{}"'.format(container["Name"]))

    def _process_container_image(self, item, container):
        """update the image informations for the current container"""
        container['Image'] = self.bind_data('{{account_id}}.dkr.ecr.{{region}}.amazonaws.com/{{name}}:{{version}}') 
        if 'image' in item:
            container['Image'] = self.bind_data(item['image'])
        self._log_information(key='Image', value=container["Image"], indent=1)

    def _process_container_cpu(self, item, container):
        """update the cpu informations for the current container"""
        container['Cpu'] = 128
        if 'cpu' in item:
            container['Cpu'] = int(item['cpu'])
        self._log_information(key='Cpu', value=container["Cpu"], indent=1)

    def _process_container_memory(self, item, container):
        """update the memory informations for the current container"""
        container['Memory'] = 128
        if 'memory' in item:
            container['Memory'] = int(item['memory'])
        self._log_information(
            key='Memory', value=container["Memory"], indent=1)

    def _process_container_memory_reservation(self, item, container):
        """update the memory reservation informations for the current container"""
        if 'memory_reservation' in item:
            container['MemoryReservation'] = int(item['memory_reservation'])
            self._log_information(key='Memory Reservation',
                                  value=container["MemoryReservation"], indent=1)

    def _process_container_port_mappings(self, item, container):
        """update the port mappings informations for the current container"""
        if 'port_mappings' in item:
            container['PortMappings'] = []
            self._log_information(key='Port mappings', value='', indent=1)
            for p in item['port_mappings']:
                port_mapping = {
                                'HostPort': 0,
                                'ContainerPort': int(p['container_port'])
                                }
                if 'host_port' in p:
                    if isinstance(p['host_port'], int):
                        port_mapping['HostPort'] = p['host_port']
                    elif 'green' in p['host_port'] and 'blue' in p['host_port']:
                        port_mapping['HostPort'] = int(p['host_port'][self.infos.elected_release])
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
                container['PortMappings'].append(port_mapping)
                self._log_information(key='- '+protocol, value='{} -> {}'.format(
                    host_port, port_mapping['ContainerPort']), indent=2)

    def _process_container_entry_point(self, item, container):
        """update the entry point informations for the current container"""
        if 'entry_point' in item:
            container['EntryPoint'] = ','.join(item['entry_point'])
            self.logger.info(f'     Entry point : {container["EntryPoint"]}')

    def _process_container_environment(self, item, container):
        """update the environment informations for the current container"""
        container['Environment'] = []
        if 'environment' in item:
            for elmt in item['environment']:
                e = {}
                for k, v in elmt.items():
                    e['Name'] = k
                    e['Value'] = v
                e['Value'] = self.bind_data(str(v))
                container['Environment'].append(e)
        # ajout variable d'environement par défault
        self._add_default_environment_variable(
            container, 'AWS_ENVIRONMENT', '{{environment}}')
        self._add_default_environment_variable(
            container, 'AWS_REGION', '{{region}}')
        self._add_default_environment_variable(
            container, 'AWS_ACCOUNT_ID', '{{account_id}}')
        self._log_information(key='Environment', value='', indent=1)
        for e in container['Environment']:
            self._log_information(
                key='- '+e['Name'], value=e['Value'], indent=2)

    def _process_container_secrets(self, item, container):
        """update the secrets informations for the current container"""
        container['Secrets'] = []
        if 'secrets' in item:
            self._log_information(key='Secrets', value='', indent=1)
            for elmt in item['secrets']:
                #TODO A retravailler
                e = {}
                for a in elmt.keys():
                    e['Name'] = a
                e['ValueFrom'] = None
                for a in elmt.values():
                    e['ValueFrom'] = a
                    e['ValueFrom'] = self.bind_data(e['ValueFrom'])
                for s in self.infos.secret_infos.secrets:
                    if s['id'] == e['ValueFrom']:
                        e['ValueFrom'] = s['arn']
                container['Secrets'].append(e)
                self._log_information(
                    key='- '+e['Name'], value=e['ValueFrom'], indent=2)

    def _process_container_command(self, item, container):
        """update the command informations for the current container"""
        if 'command' in item:
            self._log_information(key='Command', value='', indent=1)
            container['Command'] = []
            for e in item['command']:
                container['Command'].append(e)
                self._log_information(key='- '+e, value=None, indent=2)

    def _process_container_dns_search_domains(self, item, container):
        """update the dns search domain informations for the current container"""
        if 'dns_search_domains' in item:
            self._log_information(key='Dns Search Domains', value='', indent=1)
            container['DnsSearchDomains'] = []
            for e in item['dns_search_domains']:
                container['DnsSearchDomains'].append(e)
                self._log_information(key='- '+e, value=None, indent=2)

    def _process_container_disable_networking(self, item, container):
        """update the disable networking informations for the current container"""
        if 'disable_networking' in item:
            if str(item['disable_networking']).lower().strip() == 'true':
                container['DisableNetworking'] = "true"
            else:
                container['DisableNetworking'] = "false"
            self._log_information(
                key='Disable networking', value=container["DisableNetworking"], ljust=10, indent=1)

    def _process_container_dns_servers(self, item, container):
        """update the dns servers informations for the current container"""
        if 'dns_servers' in item:
            self._log_information(key='Dns Servers', value='', indent=1)
            container['DnsServers'] = []
            for e in item['dns_servers']:
                container['DnsServers'].append(e)
                self._log_information(key='- '+e, value=None, indent=2)

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
            if item['essential'].lower().strip() == 'true':
                container['Essential'] = "true"
            else:
                container['Essential'] = "false"
        self._log_information(
            key='Essential', value=container["Essential"], indent=1)

    def _process_container_privileged(self, item, container):
        """update the privileged informations for the current container"""
        if 'privileged' in item:
            if str(item['privileged']).lower().strip() == 'true':
                container['Privileged'] = "true"
            else:
                container['Privileged'] = "false"
            self._log_information(
                key='Priviliged', value=container["Privileged"], indent=1)

    def _process_container_mount_points(self, item, container):
        """update the mount points informations for the current container"""
        if 'mount_points' in item:
            self._log_information(key='Mount points', value='', indent=1)
            container['MountPoints'] = []
            for e in item['mount_points']:
                mount_point = {}
                mount_point['ContainerPath'] = self.bind_data(e['container_path'])
                self._log_information(
                    key='- Container Path', value=mount_point["ContainerPath"], indent=2)
                mount_point['SourceVolume'] = self.bind_data(e['source_volume'])
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

    def _process_container_hostname(self, item, container):
        """update the hostname informations for the current container"""
        if 'hostname' in item:
            container['Hostname'] = item['hostname']
            self._log_information(
                key='Hostname', value=container["Hostname"], indent=1)

    def _process_container_start_timeout(self, item, container):
        """update the start timeout informations for the current container"""
        if 'start_timeout' in item:
            container['StartTimeout'] = int(item['start_timeout'])
            self._log_information(key='Start Timeout',
                                  value=container["StartTimeout"], indent=1)

    def _process_container_stop_timeout(self, item, container):
        """update the stop timeout informations for the current container"""
        if 'stop_timeout' in item:
            container['StopTimeout'] = int(item['stop_timeout'])
            self._log_information(key='Stop timeout',
                                  value=container["StopTimeout"], indent=1)

    def _process_container_log_configuration(self, item, container):
        container['LogConfiguration'] = {}
        container['LogConfiguration']['LogDriver'] = 'awslogs'
        container['LogConfiguration']['Options'] = {}
        container['LogConfiguration']['Options'][
            'awslogs-group'] = f'/aws/ecs/{self.infos.cluster_name}/service/{self.infos.service_name}'
        container['LogConfiguration']['Options']['awslogs-region'] = self.infos.region
        container['LogConfiguration']['Options']['awslogs-stream-prefix'] = self.infos.service_version
        self._log_information(key='Log Configuration', value='', indent=1)
        self._log_information(
            key='Log Driver', value=container['LogConfiguration']['LogDriver'], indent=2)
        self._log_information(key='Options', value='', indent=2)
        self._log_information(
            key='- awslogs-group', value=container['LogConfiguration']['Options']['awslogs-group'], indent=3)
        self._log_information(
            key='- awslogs-region', value=container['LogConfiguration']['Options']['awslogs-region'], indent=3)
        self._log_information(key='- awslogs-stream-prefix',
                              value=container['LogConfiguration']['Options']['awslogs-stream-prefix'], indent=3)

    def _process_depends_on(self, item, container):
        """update the depends on for the current container"""
        if 'depends_on' in item:
            container['DependsOn'] = []
            self._log_information(key='Depend On', value='', indent=1)
            for i in item['depends_on']:
                depends_on = {}
                depends_on['Condition'] = i['condition']
                depends_on['ContainerName'] = i['container_name']
                container['DependsOn'].append(depends_on)
                self._log_information(
                    key='- ContainerName', value=depends_on['ContainerName'], indent=2)
                self._log_information(
                    key='  Condition', value=depends_on['Condition'], indent=2)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.infos.secret_infos = self._find_secrets_task_informations()
            cfn = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['ContainerDefinitions']
            for item in self.configuration['service']['containers']:
                container = {}
                self._process_container_name(item, container)
                self._process_container_image(item, container)
                self._process_container_cpu(item, container)
                self._process_container_memory(item, container)
                self._process_container_memory_reservation(item, container)
                self._process_container_port_mappings(item, container)
                self._process_container_entry_point(item, container)
                self._process_container_environment(item, container)
                self._process_container_secrets(item, container)
                self._process_container_command(item, container)
                self._process_container_dns_search_domains(item, container)
                self._process_container_disable_networking(item, container)
                self._process_container_dns_servers(item, container)
                self._process_container_docker_security_options(
                    item, container)
                self._process_container_essential(item, container)
                self._process_container_links(item, container)
                self._process_container_privileged(item, container)
                self._process_container_mount_points(item, container)
                self._process_container_hostname(item, container)
                self._process_container_log_configuration(item, container)
                self._process_container_start_timeout(item, container)
                self._process_container_stop_timeout(item, container)
                self._process_depends_on(item, container)
                cfn.append(container)
            self.infos.save()
            return PrepareDeploymentServiceDefinitionStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

    def _add_default_environment_variable(self, container, key, value):
        """add a new default environment variables if not exists"""
        if not any(filter(lambda x: x['Name'] == key, container['Environment'])):
            env = {}
            env['Name'] = key
            env['Value'] = self.bind_data(value)
            container['Environment'].append(env)

    def _find_secrets_task_informations(self):
        """find secret task information for vault resolution in excution task role."""
        result = None
        o = []

        for container_infos in self.configuration['service']['containers']:
            if 'secrets' in container_infos:
                for item in container_infos['secrets']:
                    format = self.bind_data(str(item)).replace('\'', '"')
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
