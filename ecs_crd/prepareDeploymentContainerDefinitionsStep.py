import json
import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.canaryReleaseInfos import SecretInfos
from ecs_crd.prepareDeploymentServiceDefinitionStep import PrepareDeploymentServiceDefinitionStep

class PrepareDeploymentContainerDefinitionsStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Container definitions )', logger)

    def _process_container_name(self, item, container):
        """update the name informations for the current container"""
        container['Name'] = 'default'
        if 'name' in item:
            container['Name'] = item['name']
        self.logger.info(f' Container "{container["Name"]}"')
    
    def _process_container_image(self, item, container):
        """update the image informations for the current container"""
        container['Image'] =  self.bind_data('{{account_id}}.dkr.ecr.{{region}}.amazonaws.com/{{name}}:{{version}}')
        if 'image' in item:
            container['Image'] = self.bind_data(item['image'])
        self.logger.info(f'     Image   : {container["Image"]}')

    def _process_container_cpu(self, item, container):
        """update the cpu informations for the current container"""
        container['Cpu']= 128
        if 'cpu' in item:
            container['Cpu'] = int(item['cpu'])
        self.logger.info(f'     Cpu     : {container["Cpu"]}')

    def _process_container_memory(self, item, container):
        """update the memory informations for the current container"""
        container['Memory'] = 128
        if 'memory' in item:
            container['Memory'] = int(item['memory'])
        self.logger.info(f'     Memory  : {container["Memory"]}')

    def _process_container_memory_reservation(self, item, container):
        """update the memory reservation informations for the current container"""
        if 'memory_reservation' in item:
            container['MemoryReservation'] = int(item['memory_reservation'])
            self.logger.info(f'     Memory Reservation : {container["MemoryReservation"]}') 

    def _process_container_port_mappings(self, item, container):
        """update the port mappings informations for the current container"""
        if 'port_mappings' in item:
            container['PortMappings'] = []
            self.logger.info(f'     Port mappings : ')
            for p in item['port_mappings']:
                port_mapping = {}
                port_mapping['HostPort'] = 0
                port_mapping['ContainerPort'] = int(p['container_port'])
                if 'host_port' in p:
                    if self.is_int(p['host_port']):
                        port_mapping['HostPort'] = p['host_port']
                    else:
                        if 'green' in p['host_port'] and 'blue' in p['host_port']:
                            port_mapping['HostPort'] = int(p['host_port'][self.infos.elected_release])
                protocol = 'tcp'
                host_port = ''
                if port_mapping['HostPort']==0:
                    host_port = '"dynamic"'
                else:
                    host_port = '{} ({})'.format(port_mapping['HostPort'], self.infos.elected_release)
                if 'protocol' in p:
                    protocol = p['protocol']
                    port_mapping['Protocol'] = protocol
                container['PortMappings'].append(port_mapping)
                self.logger.info('          {} : {} -> {}'.format(protocol, host_port, port_mapping['ContainerPort']))

    def _process_container_entry_point(self, item, container):
        """update the entry point informations for the current container"""
        if 'entry_point' in item:
            container['EntryPoint'] = ','.join(item['entry_point'])
            self.logger.info(f'     Entry point : {container["EntryPoint"]}')

    def _process_container_environment(self, item, container):
        """update the environment informations for the current container"""
        container['Environment'] = []
        if 'environment' in item:
            self.logger.info(f'     Environment : ')
            for elmt in item['environment']:
                e = {}
                for a in elmt.keys():
                    e['Name'] = a
                for a in elmt.values():
                    e['Value'] = a
                e['Value'] = self.bind_data(str(e['Value']))
                container['Environment'].append(e)
                
        # ajout variable d'environement par défault
        self._add_default_environment_variable(container,'AWS_ENVIRONMENT','{{environment}}')
        self._add_default_environment_variable(container,'AWS_REGION','{{region}}')
        self._add_default_environment_variable(container,'AWS_ACCOUNT_ID','{{account_id}}')
        for e in container['Environment']:
            self.logger.info('          {} : {}'.format(e['Name'],e['Value']))

    def _process_container_secrets(self, item, container):
        """update the secrets informations for the current container"""
        container['Secrets'] = []
        if 'secrets' in item:
            self.logger.info(f'     Secrets : ')
            for elmt in item['secrets']:
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
                self.logger.info('          {} : {}'.format(e['Name'],e['ValueFrom']))


    def _process_container_command(self, item, container):
        """update the command informations for the current container"""
        if 'command' in item:
            self.logger.info(f'     Command : ')
            container['Command']=[]
            for e in item['command']:
                container['Command'].append(e)
                self.logger.info('          {}'.format(e))

    def _process_container_dns_search_domains(self, item, container):
        """update the dns search domain informations for the current container"""
        if 'dns_search_domains' in item:
            self.logger.info(f'     Dns Search Domains : ')
            container['DnsSearchDomains']=[]
            for e in item['dns_search_domains']:
                container['DnsSearchDomains'].append(e)
                self.logger.info('          {}'.format(e))

    def _process_container_disable_networking(self, item, container):
        """update the disable networking informations for the current container"""
        if 'disable_networking' in item:
            if item['disable_networking'].lower().strip() == 'true':
                container['DisableNetworking'] = "true"     
            else:
                container['DisableNetworking'] = "false"  
            self.logger.info(f'     Disable networking : {container["DisableNetworking"]}') 

    def _process_container_dns_servers(self, item, container):
        """update the dns servers informations for the current container"""
        if 'dns_servers' in item:
            self.logger.info(f'     Dns Servers : ')
            container['DnsServers']=[]
            for e in item['dns_servers']:
                container['DnsServers'].append(e)
                self.logger.info('          {}'.format(e))

    def _process_container_docker_security_options(self, item, container):
        """update the docker security informations for the current container"""
        if 'docker_security_options' in item:
            self.logger.info(f'     Docker Security Options : ')
            container['DockerSecurityOptions']=[]
            for e in item['docker_security_options']:
                container['DockerSecurityOptions'].append(e)
                self.logger.info('          {}'.format(e))

    def _process_container_essential(self, item, container):
        """update the essential informations for the current container"""
        if 'essential' in item:
            if item['essential'].lower().strip() == 'true':
                container['Essential'] = "true"     
            else:
                container['Essential'] = "false"                           
            self.logger.info(f'     Essential : {container["Essential"]}') 
    
    def _process_container_links(self, item, container):
        """update the links informations for the current container"""
        if 'privileged' in item:
            if item['privileged'].lower().strip() == 'true':
                container['Privileged'] = "true"     
            else:
                container['Privileged'] = "false"
            self.logger.info(f'     Priviliged : {container["Privileged"]}')

    def _process_container_mount_points(self, item, container):
        """update the mount points informations for the current container"""
        if 'mount_points' in item:
            self.logger.info(f'     Mount points : ')
            container['MountPoints'] = []
            for e in item['mount_points']:
                mount_point = {}
                mount_point['ContainerPath'] = e['container_path']   
                self.logger.info(f'         Container Path : {mount_point["ContainerPath"]}')
                mount_point['SourceVolume'] = e['source_volume']
                self.logger.info(f'         Source Volume : {mount_point["SourceVolume"]}')
                if 'read_only' in e:
                    if e['read_only'].lower().strip() == 'true':
                        mount_point['ReadOnly'] = "true"     
                    else:
                        mount_point['ReadOnly'] = "false"
                    self.logger.info(f'         Read  Only : {mount_point["ReadOnly"]}')
                container['MountPoints'].append(mount_point)
    
    def _process_container_hostname(self, item, container):
        """update the hostname informations for the current container"""
        if 'hostname' in item:
            container['Hostname'] = item['hostname']
            self.logger.info(f'     Mount points : {container["Hostname"]}')

    def _process_container_start_timeout(self, item , container):
        """update the start timeout informations for the current container"""
        if 'start_timeout' in item:
            container['StartTimeout'] = int(item['start_timeout'])
            self.logger.info(f'     Start timeout : {container["StartTimeout"]}')

    def _process_container_stop_timeout(self, item , container):
        """update the stop timeout informations for the current container"""
        if 'stop_timeout' in item:
            container['StopTimeout'] = int(item['stop_timeout'])
            self.logger.info(f'     Stop timeout : {container["StopTimeout"]}')

    def _process_container_log_configuration(self, item, container):
        container['LogConfiguration'] = {}
        container['LogConfiguration']['LogDriver'] = 'awslogs'
        container['LogConfiguration']['Options'] = {}
        container['LogConfiguration']['Options']['awslogs-group'] = f'/aws/ecs/{self.infos.cluster_name}/service/{self.infos.service_name}'
        container['LogConfiguration']['Options']['awslogs-region'] = self.infos.region
        container['LogConfiguration']['Options']['awslogs-stream-prefix'] = self.infos.service_version
    
    def _process_depends_on(self, item, container):
        """update the depends on for the current container"""
        if 'depends_on' in item:
            container['DependsOn'] = []
            self.logger.info(f'     Depends on :')
            for i in item['depends_on']:
                depends_on = {}
                depends_on['Condition'] = i['condition']
                self.logger.info(f'         Condition : {depends_on["Condition"]}')
                depends_on['ContainerName'] = i['container_name']
                self.logger.info(f'         ContainerName : {depends_on["ContainerName"]}')
                container['DependsOn'].add(depends_on)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.logger.info('')
            self.logger.info('Container definitions infos :')
            self.logger.info(''.ljust(50, '-'))

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
                self._process_container_docker_security_options(item, container)
                self._process_container_essential(item, container)
                self._process_container_links(item, container)
                self._process_container_mount_points(item, container)
                self._process_container_hostname(item, container)
                self._process_container_log_configuration(item, container)
                self._process_depends_on(item, container)
                self._process_container_start_timeout(item, container)
                self._process_container_stop_timeout(item, container)
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
        if len(list(filter(lambda x: x['Name']==key, container['Environment'])))==0:
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
        if (len(o)==0):
            return None
        # secrets exist 
        result = SecretInfos()
        client = boto3.client('secretsmanager', region_name = self.infos.region)
        kmsKeyIds = []
        for item in o:
            for k in item.keys():
                secretId = item[k]
                try:
                    response = client.describe_secret( SecretId=secretId )
                    if response['ARN'] not in result.secrets_arn:
                        a = {}
                        a['id']=item[k]
                        a['arn']=response['ARN']
                        result.secrets.append(a)
                        result.secrets_arn.append(response['ARN'])
                        if response['KmsKeyId'] not in kmsKeyIds:
                            kmsKeyIds.append(response['KmsKeyId'])
                except Exception as e:
                    raise ValueError(f'Invalid secret: {secretId}, reason:{e}')
                    
        client = boto3.client('kms',  region_name = self.infos.region)
        for k in kmsKeyIds:
            response = client.describe_key(KeyId=k, GrantTokens=['DescribeKey'])
            result.kms_arn.append(response['KeyMetadata']['Arn'])
        return result
