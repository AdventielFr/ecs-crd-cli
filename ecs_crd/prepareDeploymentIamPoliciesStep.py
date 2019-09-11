from ecs_crd.canaryReleaseInfos import PolicyInfos
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentStrategyStep import PrepareDeploymentStrategyStep

class PrepareDeploymentIamPoliciesStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( IAM Role & Policies )', logger)

    def _find_all_dto_policies(self):
        """find all dto policies """
        result = []
        if 'policies' in self.configuration["service"]:
            count = 1
            for item in self.configuration['service']['policies']:
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
                        resources.append(self.bind_data(r))
                actions = item['actions']
                result.append(PolicyInfos(name, effect, actions, resources))
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
        cfn_policy_item['Action'] = policy_info.action
        cfn_policy_item['Resource'] = policy_info.resource
        cfn_policy['PolicyDocument']['Statement'].append(cfn_policy_item)
        self.logger.info(f'  Policy "{policy_info.name}"')
        self.logger.info(f'     Effect : {policy_info.effect}')
        self.logger.info(f'     Action : ')
        for a in policy_info.action:
            self.logger.info(f'         {a}')
        self.logger.info(f'     Resource : ')
        for a in policy_info.resource:
            self.logger.info(f'         {a}')
        self.logger.info('')
        return cfn_policy

    def _process_task_role(self):
        """update the role for the ECS task service"""
        policies = self._find_all_dto_policies()
        if len(policies)>0:
            cfn_policies = []
            self.logger.info('')
            self.logger.info(' Task role policy infos :')
            self.logger.info('')
            for policy in policies:
                cfn_policies.append(self._policy_info_2_cloud_formation_policy(policy))
            role = {}
            role['Type'] = 'AWS::IAM::Role'
            role['Properties'] = {}
            role['Properties']['RoleName'] = f'{self.infos.environment}-{self.infos.service_name}-{self.infos.green_infos.canary_release}-ecs-task-role'
            role['Properties']['Policies'] = cfn_policies
            role['Properties']['AssumeRolePolicyDocument'] = {}
            role['Properties']['AssumeRolePolicyDocument']['Version'] = '2012-10-17'
            role['Properties']['AssumeRolePolicyDocument']['Statement'] = []
            item = {}
            item['Effect']='Allow'
            item['Principal'] = {}
            item['Principal']['Service'] = []
            item['Principal']['Service'].append('ecs-tasks.amazonaws.com')
            item['Action'] = []
            item['Action'].append('sts:AssumeRole')
            role['Properties']['AssumeRolePolicyDocument']['Statement'].append(item)
            self.infos.green_infos.stack['Resources']['TaskRole'] = role
            self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['TaskRoleArn'] = {}
            self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['TaskRoleArn']['Ref'] = 'TaskRole'
    
    def _process_task_execution_role(self):
        """update the role for ECS task execution"""
        if self.infos.secret_infos != None:
            self.logger.info('')
            self.logger.info(' Task execution role policy infos :')
            self.logger.info('')
            cfn_policies = []
            effect = 'Allow'
            action = ['kms:Decrypt','secretsmanager:GetSecretValue']
            resource = self.infos.secret_infos.secrets_arn + self.infos.secret_infos.kms_arn
            policy = PolicyInfos('AllowReadSecrets', effect, action,resource)
            cfn_policies.append(self._policy_info_2_cloud_formation_policy(policy))
            self.infos.green_infos.stack['Resources']['TaskExecutionRole']['Properties']['Policies'] = cfn_policies

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_task_role()
            self._process_task_execution_role()
            self.infos.save()
            return PrepareDeploymentStrategyStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

   