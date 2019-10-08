#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ecs_crd.canaryReleaseInfos import PolicyInfos
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentStrategyStep import PrepareDeploymentStrategyStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentIamPoliciesStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( IAM Role & Policies )', logger)

    def _convert_to_dto_policy_info(self, item, count):
        name = f'policy_{count}'
        if 'name' in item:
            name = item['name']
        resources = []
        effect = "Allow"
        if 'effect' in item:
            effect = item['effect']
        if 'resources' not in item:
            resources.append('*')
        else:
            for r in item['resources']:
                resources.append(self._bind_data(r))
        actions = item['actions']
        return PolicyInfos(
            name = name, 
            effect =effect, 
            actions = actions, 
            resources =resources)

    def _find_all_task_role_policies(self):
        """find all task role policies policies """
        result = []
        if 'iam_roles' in self.configuration["service"] and 'task_role' in self.configuration["service"]['iam_roles']:
            count = 1
            for item in self.configuration['service']['iam_roles']['task_role']:
                result.append(self._convert_to_dto_policy_info(item, count))
        return result

    def _find_all_task_execution_role_policies(self):
        """find all task execution role policies """
        result = []
        if 'iam_roles' in self.configuration["service"] and 'task_execution_role' in self.configuration["service"]['iam_roles']:
            count = 1
            for item in self.configuration['service']['iam_roles']['task_execution_role']:
                result.append(self._convert_to_dto_policy_info(item, count))
        
        # add secret policy
        if self.infos.secret_infos:
            cfn_policies = []
            effect = 'Allow'
            actions = ['kms:Decrypt', 'secretsmanager:GetSecretValue']
            resources = self.infos.secret_infos.secrets_arn + self.infos.secret_infos.kms_arn
            result.append(PolicyInfos(
                name = 'AllowReadSecrets', 
                effect = effect, 
                actions = actions, 
                resources = resources ))
        return result

    def _policy_info_2_cloud_formation_policy(self, policy_info):
        """convert a dto policy to cloud formation IAM policy"""
        cfn_policy = {}
        cfn_policy['PolicyName'] = policy_info.name
        cfn_policy['PolicyDocument'] = {}
        cfn_policy['PolicyDocument']['Version'] = "2012-10-17"
        cfn_policy['PolicyDocument']['Statement'] = []
        cfn_policy_item = {}
        cfn_policy_item['Effect'] = policy_info.effect
        cfn_policy_item['Action'] = policy_info.actions
        cfn_policy_item['Resource'] = policy_info.resources
        cfn_policy['PolicyDocument']['Statement'].append(cfn_policy_item)
        self.logger.info('')
        self._log_information(key='Sid', value=policy_info.name, indent=1)
        self._log_information(key='Effect', value=policy_info.effect, indent=2)
        self._log_information(key='Action', value='', indent=2)
        for a in policy_info.actions:
            self._log_information(key='- '+a, value=None, indent=3)
        self._log_information(key='Resource', value='', indent=2)
        for a in policy_info.resources:
            self._log_information(key='- '+a, value=None, indent=3)
        return cfn_policy

    def _process_task_role(self):
        """update the role for the ECS task service"""
        policies = self._find_all_task_role_policies()
        if policies:
            #TODO Revoir la creation du HASH
            self._log_sub_title('Task role definition')
            self.logger.info('')
            role = {}
            role['Type'] = 'AWS::IAM::Role'
            role['Properties'] = {}
            role['Properties']['RoleName'] = self._generate_name(suffix='-ecs-task', canary_release=self.infos.green_infos.canary_release)
            self._log_information(key='Name', value=role['Properties']['RoleName'])
            role['Properties']['AssumeRolePolicyDocument'] = {}
            role['Properties']['AssumeRolePolicyDocument']['Version'] = '2012-10-17'
            role['Properties']['AssumeRolePolicyDocument']['Statement'] = []
            item = {}
            item['Effect'] = 'Allow'
            item['Principal'] = {}
            item['Principal']['Service'] = []
            item['Principal']['Service'].append('ecs-tasks.amazonaws.com')
            item['Action'] = []
            item['Action'].append('sts:AssumeRole')
            role['Properties']['AssumeRolePolicyDocument']['Statement'].append(item)
            cfn_policies = []
            policy_infos = self._find_all_task_role_policies()
            for policy_info in policy_infos:
                cfn_policies.append(self._policy_info_2_cloud_formation_policy(policy_info))
            role['Properties']['Policies'] = cfn_policies
            self.infos.green_infos.stack['Resources']['TaskRole'] = role
            self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['TaskRoleArn'] = {}
            self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['TaskRoleArn']['Ref'] = 'TaskRole'

    def _process_task_execution_role(self):
        """update the role for ECS task execution"""
        self.logger.info('')
        self._log_sub_title('Task execution role definition')
        self.logger.info('')
        self.infos.green_infos.stack['Resources']['TaskExecutionRole']['Properties']['RoleName'] = self._generate_name(suffix='-ecs-exec-task', canary_release=self.infos.green_infos.canary_release)
        self._log_information(key='Name', value=self.infos.green_infos.stack['Resources']['TaskExecutionRole']['Properties']['RoleName'])
        policy_infos = self._find_all_task_execution_role_policies()
        if policy_infos:
            cfn_policies = []
            for policy_info in policy_infos:
                cfn_policies.append(self._policy_info_2_cloud_formation_policy(policy_info))
            self.infos.green_infos.stack['Resources']['TaskExecutionRole']['Properties']['Policies'] = cfn_policies

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_task_role()
            self._process_task_execution_role()
            self.infos.save()
            return PrepareDeploymentStrategyStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 9
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)