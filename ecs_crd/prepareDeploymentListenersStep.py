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
        self.current_priority = None

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

                listener_rule_infos = self._find_listener_rule_infos(listener_infos)
                # not exist listener rule , then create a new listener
                if not listener_rule_infos:
                    self._process_listener(listener_infos, item, target_group, container_name, container_port)
                else:
                # else create listener rules
                    self._process_listener_rules(listener_rule_infos, item, target_group, container_name, container_port)

            self.infos.save()
            return PrepareDeploymentIamPoliciesStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 8
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)

    def _process_listener_rules(self, listener_rule_infos, item, target_group, container_name, container_port):
        """convert listener dto informations to cloudformation List of Application Load Balancer Listener rules"""
        host_port = str(self._find_host_port(container_name, container_port))
        host_port = '(dynamic)' if host_port == '0' else host_port
        self._log_sub_title(f'Container "{container_name}:{container_port}"')
        self._log_information(key="Arn",value=listener_rule_infos.listener_arn, indent=1)
        self._log_information(key="Port", value=listener_rule_infos.configuration['port'], indent=1)
        self._log_information(key="Rules", value='', indent=1)
        # rules
        count = 1
        for rule in listener_rule_infos.configuration['rules']:
            resource_key = item['TargetGroupArn']['Ref'].replace('TargetGroup', f'ListenerRule{count}')
            self.infos.green_infos.stack['Resources'][resource_key] = self._convert_2_listener_rule(listener_rule_infos, item, rule)
            count +=1
        # certificates
        certificates = self._find_certificates(listener_rule_infos.configuration)
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

    def _find_listener_rule_infos(self, listener_infos):
        """check if the AWS Application Load Balancer Listerner exist"""
        listener = None
        client = boto3.client('elbv2', region_name=self.infos.region)
        response = client.describe_listeners(LoadBalancerArn=self.infos.green_infos.alb_arn)
        for item in response['Listeners']:
            if int(item['Port']) == int(listener_infos['port']):
                listener = item
                break
        if listener:
            for item in self.infos.listener_rules_infos:
                if item.configuration == listener_infos:
                    item.listener_arn = listener['ListenerArn']
                    item.current_priority = self._find_last_listener_rule_priority(item)    
                    return item

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

    def _convert_2_listener_rule(self, listener_rule_infos, item, rule):
        listener_rule = {}
        listener_rule['Type'] = "AWS::ElasticLoadBalancingV2::ListenerRule"
        listener_rule['Properties'] = {}
        listener_rule['Properties']['Priority'] = self._calculate_avalaible_priority_rule(listener_rule_infos, rule)
        listener_rule['Properties']['ListenerArn'] = listener_rule_infos.listener_arn
        self._log_information(key="- Priority",value=str(listener_rule['Properties']['Priority']), indent=2)
        # actions
        listener_rule['Properties']['Actions'] = []
        self._log_information(key="Actions",value='', indent=4)
        order = 1
        add_default_action = True
        if 'actions' in rule:
            for action in rule['actions']:
                action, is_default_action = self._convert_2_action(action, order)
                listener_rule['Properties']['Actions'].append(action)
                if is_default_action:
                    add_default_action = False
                order +=1
        # add default forward action to container target group
        if add_default_action:
            action, is_default_action = self._convert_2_action_forward(item, order)
            listener_rule['Properties']['Actions'].append(action)
        
        # conditions
        listener_rule['Properties']['Conditions'] = []
        if 'conditions' in rule:
            self._log_information(key="Conditions",value='', indent=4)
            for condition in rule['conditions']:
                listener_rule['Properties']['Conditions'].append(self._convert_2_condition(condition))
        return listener_rule
    
    def _find_last_listener_rule_priority(self, listener_rule_infos):
        client = boto3.client('elbv2', region_name = self.infos.region)
        response = client.describe_rules(ListenerArn = listener_rule_infos.listener_arn)
        priorities = [2]
        for item in response['Rules']:
            priority = self._to_int(item['Priority'])
            if priority:
                priorities.append(priority)
        return max(priorities, key=lambda x:x) + 1
        
    def _find_host_port(self, container_name, container_port):
        """ find the host port for the tupe container name / container port"""
        cfn_container_definitions = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['ContainerDefinitions']
        container_info = next((x for x in cfn_container_definitions if x['Name'] == container_name), None)
        return next((x for x in container_info['PortMappings'] if str(x['ContainerPort']) == str(container_port)), None)['HostPort']

    def _calculate_avalaible_priority_rule(self, listener_rule_infos, rule):
        """calculate avalaible priority rule"""
        result = None
        if 'priority' in rule:
            return rule['priority']
        else:
            result = listener_rule_infos.current_priority
            listener_rule_infos.current_priority += 1
            return result

    def _convert_2_condition(self, item):
        condition = {}
        self._process_property(
            source = item,
            target = condition,
            pattern= 'host-header|http-header|http-request-method|path-pattern|source-ip',
            source_property = 'field',
            indent = 5,
            multi = True
        )
        property_name = None
        if condition['Field'] == 'host-header':
            property_name = 'HostHeaderConfig'
        elif condition['Field'] == 'http-header':
            property_name = 'HttpHeaderConfig'
        elif condition['Field'] == 'http-request-method':
            property_name = 'HttpRequestMethodConfig'
        elif condition['Field'] == 'path-pattern':
            property_name = 'PathPatternConfig'
        else:
            property_name = 'SourceIpConfig'

        condition[property_name] = {}
        self._log_information(key=property_name,value='',indent=7)
        condition[property_name]['Values'] = []
        self._log_information(key='Values',value='',indent=9)
        for v in item['values']:
            data = self._bind_data(v)
            condition[property_name]['Values'].append(data)
            self._log_information(key='- ' +data,value=None,indent=11)

        return condition

    def _convert_2_action_forward(self, item, order):
        action = {}
        action['Type'] = 'forward'
        action['Order'] = order
        action['TargetGroupArn'] = {}
        action['TargetGroupArn']['Ref'] = item['TargetGroupArn']['Ref']
        self._log_information(key=f'- Type', value = action['Type'], indent=5)
        self._log_information(key=f'Order', value = action['Order'], indent=7)
        self._log_information(key='TargetGroupArn', value ='-> container target group created', indent=7)
        return action, True

    def _convert_2_action(self, item, order):
        action = {}
        is_default_action = False
        # action type
        self._process_property(
            source = item,
            target = action,
            pattern= 'authenticate-oidc|authenticate-cognito|fixed-response|redirect',
            source_property = 'type',
            indent = 5,
            multi = True
        )
        action['Order'] = order if 'order' not in item else item['order']
        self._log_information(key='Order',value=action['Order'],indent=7)
        property_name = None
        if action['Type'] == 'authenticate-oidc':
            property_name = 'AuthenticateOidcConfig'
        elif action['Type'] == 'authenticate-cognito':
            property_name = 'AuthenticateCognitoConfig'
        elif action['Type'] == 'fixed-response':
            property_name = 'FixedResponseConfig'
            is_default_action = True
        else:
            property_name = 'RedirectConfig'
            is_default_action = True
        
        if property_name:
            action[property_name]= {}
            self._log_information(key=property_name,value='',indent=7)
            for k in item['config'].keys():
                key = self._to_pascal_case(k)
                src = item['config'][k]
                if isinstance(src, str):
                    action[property_name][key] = self._bind_data(src)
                else:
                    action[property_name][key] = src
                self._log_information(key=key,value=action[property_name][key],indent=9)
        
        return action, is_default_action
