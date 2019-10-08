#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentIamPoliciesStep import PrepareDeploymentIamPoliciesStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentListenersStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,  f'Prepare {infos.action}( Listeners )', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            cfn = self.infos.green_infos.stack['Resources']['Service']['Properties']['LoadBalancers']
            for item in cfn:
                target_group = self.infos.green_infos.stack['Resources'][item['TargetGroupArn']['Ref']]
                listener_infos = self._find_listener_infos(target_group)
                #TODO à revoir
                ttt = target_group['Properties']['Tags'] 
                container_name = next((x for x in ttt if x['Key'] == 'Container'), None)['Value']
                container_port = str(next((x for x in ttt if x['Key'] == 'ContainerPort'), None)['Value'])

                if not listener_infos:
                    container_name = next((x for x in ttt if x['Key'] == 'Container'), None)['Value']
                    raise ValueError('Not found listener informations for container "{}:{}", target group port "{}"'.format(container_name, container_port, target_group['Properties']['Port'])) 

                listerner_rule_infos = None
                if self._exist_listener(listener_infos):
                    listerner_rule_infos = self._find_listener_rule_infos(listener_infos)
                # not exist listener rule , then create listener
                if not listerner_rule_infos:
                    self._process_listener(listener_infos, item, target_group, container_name, container_port)
                else:
                # else create listener rule
                    self._process_listener_rule(listener_infos, listerner_rule_infos, item, target_group, container_name, container_port)

            self.infos.save()
            return PrepareDeploymentIamPoliciesStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 8
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)
       
    def _find_listener_rule_infos(self, listener_infos):
        """find the listener rule informations"""
        for item in self.infos.listener_rules_infos:
            if item.configuration == listener_infos:
                return item

    def _convert_2_condition_generic(self, item, condition, name):
        condition[name] = {}
        self._log_information(key=name, value='',indent=4)
        self._log_information(key='Values', value='', indent=5)
        condition[name]['Values'] = []
        for elmt in item['values']:
            data = self._bind_data(elmt)
            self._log_information(key='- '+data, value=None, indent=6)
            condition[name]['Values'].append(data)
        # unique
        cnv = condition[name]['Values']
        condition[name]['Values'] = [x for i, x in enumerate(cnv) if i == cnv.index(x)]

    def _convert_2_condition(self, item):
        condition = {}
        condition['Field'] = item['field'].lower()
        self._log_information(key='- Field', value=condition['Field'], indent=2)

        if condition['Field'] == 'host-header':
            self._convert_2_condition_generic(item, condition, 'HostHeaderConfig')

        if condition['Field'] == 'http-header':
            self._convert_2_condition_generic(item, condition, 'HttpHeaderConfig')
            data = self._bind_data(item['name'])
            condition['HttpHeaderConfig']['HttpHeaderName'] = data
            self._log_information(key='Name', value=data, indent=5)

        if condition['Field'] == 'http-request-method':
            self._convert_2_condition_generic(item, condition, 'HttpRequestMethodConfig')

        if condition['Field'] == 'path-pattern':
            self._convert_2_condition_generic(item, condition, 'PathPatternConfig')

        if condition['Field'] == 'source-ip':
            self._convert_2_condition_generic(item, condition, 'SourceIpConfig')
        return condition       

    def _process_listener_rule(self, listener_infos, listener_rule_infos, item, target_group, container_name, container_port):
        """convert listener dto informations to cloudformation Application Load Balancer Rule"""
        listener_rule = {}
        listener_rule['Type'] = "AWS::ElasticLoadBalancingV2::ListenerRule"
        listener_rule['Properties'] = {}
        listener_rule['Properties']['Priority'] = self._calculate_avalaible_priority_rule(listener_rule_infos)
        listener_rule['Properties']['ListenerArn'] = listener_rule_infos.listener_arn

        self._log_sub_title(f'Container "{container_name}:{container_port}"')

        self._log_information(key="Listerner ARN",value=listener_rule['Properties']['ListenerArn'], indent=1)
        self._log_information(key="Priority",value=str(listener_rule['Properties']['Priority']), indent=1)

        # Actions
        listener_rule['Properties']['Actions'] = []
        action = {}
        action['Type'] = 'forward'
        action['TargetGroupArn'] = {}
        action['TargetGroupArn']['Ref'] = item['TargetGroupArn']['Ref']
        listener_rule['Properties']['Actions'].append(action)

        host_port = str(self._find_host_port(container_name, container_port))
        host_port = '(dynamic)' if host_port == '0' else host_port
        self._log_information(key="Port", value=listener_infos['port'], indent=1)

        self._log_information(key="Rules", value='', indent=1)

        # Conditions
        listener_rule['Properties']['Conditions'] = []
        for condition in listener_rule_infos.configuration['rule']['conditions']:
            listener_rule['Properties']['Conditions'].append(self._convert_2_condition(condition))

        self.infos.green_infos.stack['Resources'][item['TargetGroupArn']['Ref'].replace('TargetGroup', 'ListenerRule')] = listener_rule

        # certificates
        certificates = self._find_certificates(listener_infos)
        if certificates:
            self._log_sub_title('Certificates')
            listener_certificate = {}
            listener_certificate['Type'] = 'AWS::ElasticLoadBalancingV2::ListenerCertificate'
            listener_certificate['Properties'] = {}
            listener_certificate['Properties']['Certificates'] = []
            for cert in certificates:
                certificate = {}
                certificate['CertificateArn'] = cert['CertificateArn']
                listener_certificate['Properties']['Certificates'].append(certificate)
                self._log_information(key='- DomainName', value=cert['DomainName'], indent=1)
                self._log_information(key='  ARN', value=cert['CertificateArn'], indent=1)
            listener_certificate['Properties']['ListenerArn'] = listener_rule_infos.listener_arn
            self.infos.green_infos.stack['Resources']['ListenerCertificate'] = listener_certificate

    def _process_listener(self, listener_infos, item, target_group, container_name, container_port):
        """convert listener dto informations to cloudformation Application Load Balancer Listener"""
        # Resource
        listener = {}
        listener['Type'] = "AWS::ElasticLoadBalancingV2::Listener"
        listener['Properties'] = {}
        listener['Properties']['Port'] = listener_infos['port']

        self._log_sub_title(f'Container "{container_name}:{container_port}"')

        if 'protocol' in listener_infos:
            listener['Properties']['Protocol'] = listener_infos['protocol'].upper()
        else:
            listener['Properties']['Protocol'] = 'HTTP'

        if listener['Properties']['Protocol'] == 'HTTPS':
            listener['Properties']['SslPolicy'] = 'ELBSecurityPolicy-2016-08'
            listener['Properties']['Certificates'] = []
            for cert in self._find_certificates(listener_infos):
                certificate = {}
                certificate['CertificateArn'] = cert['CertificateArn']
                listener['Properties']['Certificates'].append(certificate)

        listener['Properties']['LoadBalancerArn'] = {}
        listener['Properties']['LoadBalancerArn']['Ref'] = "LoadBalancer"

        listener['Properties']['DefaultActions'] = []
        action = {}
        action['Type'] = 'forward'
        action['TargetGroupArn'] = {}
        action['TargetGroupArn']['Ref'] = item['TargetGroupArn']['Ref']
        listener['Properties']['DefaultActions'].append(action)

        host_port = str(self._find_host_port(container_name, container_port))
        host_port = '(dynamic)' if host_port == '0' else host_port
        self._log_information(key="Port", value=listener_infos['port'], indent=1)
        cfn_resource_listener_name = item['TargetGroupArn']['Ref'].replace('TargetGroup', 'Listener')
        self.infos.green_infos.stack['Resources'][cfn_resource_listener_name] = listener

    def _find_certificates(self, listener_infos):
        """find all cerficates used by listener"""
        result = []
        if 'certificates' in listener_infos:
            client = boto3.client('acm', region_name=self.infos.region)
            response = client.list_certificates()
            for cert in response['CertificateSummaryList']:
                for certificate in listener_infos['certificates']:
                    if cert['DomainName'] == self._bind_data(certificate):
                        result.append(cert)
        return result

    def _exist_listener(self, listener_infos):
        """check if the AWS Application Load Balancer Listerner exist""" 
        client = boto3.client('elbv2', region_name=self.infos.region)
        response = client.describe_listeners(LoadBalancerArn=self.infos.green_infos.alb_arn)
        for listener in response['Listeners']:
            if int(listener['Port']) == int(listener_infos['port']):
                return True

    def _find_listener_infos(self, target_group):
        """find listener information in configuration"""
        t = target_group['Properties']['Tags']
        container_name = list(filter(lambda x: x['Key'] == 'Container', t))[0]['Value']
        container_port = int(list(filter(lambda x: x['Key'] == 'ContainerPort', t))[0]['Value'])

        for item in self.configuration['listeners']:
            port = int(item['target_group']['container']['port'])
            if container_port == port:
                listener_container_name = 'default'
                if 'name' in item['target_group']['container']:
                    listener_container_name = item['target_group']['container']['name']
                if listener_container_name.lower() == container_name.lower():
                    return item
        return None

    def _find_host_port(self, container_name, container_port):
        """ find the host port for the tupe container name / container port"""
        cfn_container_definitions = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['ContainerDefinitions']
        container_info = next((x for x in cfn_container_definitions if x['Name'] == container_name), None)
        return next((x for x in container_info['PortMappings'] if str(x['ContainerPort']) == str(container_port)), None)['HostPort']

    def _calculate_avalaible_priority_rule(self, listener_rule_infos):
        """calculate avalaible priority rule"""
        result = None
        if 'priority' in listener_rule_infos.configuration['rule']:
            result = int(listener_rule_infos.configuration['rule']['priority'])
        client = boto3.client('elbv2', region_name = self.infos.region)
        response = client.describe_rules(ListenerArn = listener_rule_infos.listener_arn)
        priorities = []
        for item in response['Rules']:
            if isinstance(item['Priority'], int):
                priorities.append(int(item['Priority']))

        priorities = sorted(priorities)
        # si il n'existe pas de priorité pour existance pour la pri
        if result:
            if result not in priorities:
                return result
            else:
                if priorities:
                    result += 1
                    while True:
                        if result not in priorities:
                            listener_rule_infos.configuration['rule']['priority'] = result
                            break
        else:
            # si la priorité n'es pas fournie
            # on met la regle en queue de priorité si ell
            if priorities:
                listener_rule_infos.configuration['rule']['priority'] = priorities[-1] + 1
            else:
                listener_rule_infos.configuration['rule']['priority'] = 1 

        return listener_rule_infos.configuration['rule']['priority'] 
