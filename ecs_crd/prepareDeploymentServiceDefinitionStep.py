#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTaskDefinitionStep import PrepareDeploymentTaskDefinitionStep


class PrepareDeploymentServiceDefinitionStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Service definition )', logger)

    def _process_scheduling_strategy(self):
        """update the sceduling stratégy informations for the service"""
        self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'REPLICA'
        if 'scheduling_strategy' in self.configuration['service']:
            if self.configuration['service']['scheduling_strategy'].upper() == 'DAEMON':
                self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'DAEMON'
        self._log_information(key='Scheduling Strategy', value=self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'], ljust=10, indent=1)

    def _process_platform_version(self):
        """update the plaform version informations for the service"""
        if 'platform_version' in self.configuration['service']:
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion'] = self.configuration['service']['platform_version']
            self._log_information(key='Platform Version', value=self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion'], ljust=10, indent=1)

    def _process_placement_constraints(self):
        """update the placement constraintes informations for the service"""
        if 'placement_constraints' in self.configuration['service']:
            self._log_information(key='Placement Contraints', value='', ljust=10, indent=1)
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'] = []
            for item in self.configuration['service']['placement_constraints']:
                constraint = {}
                if 'expression' in item:
                    constraint['Expression'] = item['expression']
                constraint['Type'] = item['type']
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'].append(constraint)
                self._log_information(key='- Expression', value=constraint['Expression'], ljust=10, indent=2)
                self._log_information(key='  Type', value=constraint['Type'], ljust=10, indent=2)

    def _process_placement_stategies(self):
        """update the placement strategies informations for the service"""
        if 'placement_stategies' in self.configuration['service']:
            self._log_information(key='Placement Strategies',value='', ljust=10, indent=1)
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'] = []
            for item in self.configuration['service']['placement_stategies']:
                strategy = {}
                strategy['Field'] = item['field']
                strategy['Type'] = item['type']
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'].append(strategy)
                self._log_information(key='- Field',value=strategy['Field'], ljust=10, indent=2)
                self._log_information(key='  Type',value=strategy['Type'], ljust=10, indent=2)

    def _process_load_balancer(self):
        cfn = self.infos.green_infos.stack['Resources']['Service']['Properties']['LoadBalancers']
        for item in self.configuration['service']['containers']:
            if 'port_mappings' in item:
                for e in item['port_mappings']:
                    definition = {}
                    container_name = 'default'
                    if 'name' in item:
                        container_name = item['name']
                    definition['ContainerName'] =  container_name
                    definition['ContainerPort'] = int(e['container_port'])
                    definition['TargetGroupArn'] = {}
                    w = definition['ContainerName'] + '_' + str(e['container_port'])
                    definition['TargetGroupArn']['Ref'] = "TargetGroup{}".format(''.join(id.capitalize() for id in w.split('_')))
                    cfn.append(definition)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_scheduling_strategy()
            self._process_platform_version()
            self._process_placement_constraints()
            self._process_placement_stategies()
            self._process_load_balancer()
            self._process_auto_scaling()
            self.infos.save()
            return PrepareDeploymentTaskDefinitionStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

    def _process_auto_scaling(self):            
        if 'auto_scaling' in self.configuration['service']:
            self._log_information(key = "AutoScaling", value='', indent=1)
            auto_scaling = self.configuration['service']['auto_scaling']
            self._process_application_autoscaling_scalable_target(auto_scaling)
            count_policy = 1
            for auto_scaling_policy in auto_scaling['auto_scaling_policies']:
                self._process_application_auto_scaling_scaling_policy(auto_scaling_policy, count_policy)
                if 'cloudwatch_alarms' in auto_scaling_policy:
                    self._log_information(key = 'CloudWatch Alarms', value='', indent=5)
                    count_cloudwatch_alarms = 1
                    for cloudwatch_alarm in auto_scaling_policy['cloudwatch_alarms']:
                        self._process_cloudwatch_alarm(cloudwatch_alarm, count_policy, count_cloudwatch_alarms)
                        count_cloudwatch_alarms = count_cloudwatch_alarms + 1
                count_policy = count_policy +1

    def _process_application_autoscaling_scalable_target(self, auto_scaling):
        cfn = {}
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalableTarget'
        properties = {}
        if 'minimum' in auto_scaling:
            properties['MinCapacity'] = int(auto_scaling['minimum'])
        else:
            properties['MinCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MinCapacity', value=properties['MinCapacity'], indent=2)
        if 'maximum' in auto_scaling:
            properties['MaxCapacity'] = int(auto_scaling['maximum'])
        else:
            properties['MaxCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MaxCapacity', value=properties['MaxCapacity'], indent=2)
        
        properties['ResourceId'] = f'service/{self.infos.cluster_name}/{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        self._log_information(key = 'ResourceId', value=properties['ResourceId'], indent=2)
        
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        self._log_information(key = 'ScalableDimension', value=properties['ScalableDimension'], indent=2)
        
        properties['ServiceNamespace'] = 'ecs'
        self._log_information(key = 'ServiceNamespace', value=properties['ServiceNamespace'], indent=2)

        properties['RoleARN'] = self.bind_data(auto_scaling['role_arn'])
        self._log_information(key = 'RoleARN', value=properties['RoleARN'], indent=2)

        cfn['Properties'] = properties
        cfn['DependsOn'] = 'Service'
        self.infos.green_infos.stack['Resources']['AutoScalingTarget'] = cfn

    def _process_application_auto_scaling_scaling_policy(self, auto_scaling_policy, count_policy):
        cfn = {}
        self._log_information(key = 'ApplicationAutoScalingScalingPolicies', value= '', indent=2)
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalingPolicy'
        properties = {}
        properties['PolicyName'] = f'{self.infos.service_name}-scaling-policy-{count_policy}'
        if 'policy_name' in auto_scaling_policy:
            properties['PolicyName']  = auto_scaling_policy['policy_name']
        self._log_information(key = '- PolicyName', value=properties['PolicyName'], indent=3)

        properties['PolicyType'] = 'StepScaling'
        self._log_information(key = 'PolicyType', value=properties['PolicyType'], indent=5)
        properties['ScalingTargetId'] =  {}
        properties['ScalingTargetId']['Ref'] = 'AutoScalingTarget'
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        self._log_information(key = 'ScalableDimension', value=properties['ScalableDimension'], indent=5)
        properties['ServiceNamespace'] = 'ecs'
        self._log_information(key = 'ServiceNamespace', value=properties['ServiceNamespace'], indent=5)
        properties['StepScalingPolicyConfiguration'] = {}
        self._log_information(key = 'StepScalingPolicyConfiguration', value='', indent=5)
        step_scaling_policy_configuration = auto_scaling_policy['step_scaling_policy_configuration']

        properties['StepScalingPolicyConfiguration']['AdjustmentType'] = 'ChangeInCapacity'
        if 'adjustment_type' in step_scaling_policy_configuration:
            properties['StepScalingPolicyConfiguration']['AdjustmentType'] = int(step_scaling_policy_configuration['adjustment_type'])
        self._log_information(key = 'AdjustmentType', value=properties['StepScalingPolicyConfiguration']['AdjustmentType'], indent=6)


        properties['StepScalingPolicyConfiguration']['Cooldown'] = 60
        if 'cooldown' in step_scaling_policy_configuration:
            properties['StepScalingPolicyConfiguration']['Cooldown'] = int(step_scaling_policy_configuration['cooldown'])
        self._log_information(key = 'Cooldown', value=properties['StepScalingPolicyConfiguration']['Cooldown'], indent=6)


        properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = 'Average'
        if 'metric_aggregation_type' in step_scaling_policy_configuration:
            properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = step_scaling_policy_configuration['metric_aggregation_type']
        self._log_information(key = 'MetricAggregationType', value=properties['StepScalingPolicyConfiguration']['MetricAggregationType'], indent=6)

        self._log_information(key = 'StepAdjustments', value='', indent=6)
        step_adjustments = []
        if 'step_adjustments' in step_scaling_policy_configuration:
             for e in auto_scaling_policy['step_scaling_policy_configuration']['step_adjustments']:
                step_adjustment = {}
                if 'metric_interval_lower_bound' in e:
                    step_adjustment['MetricIntervalLowerBound'] = int(e['metric_interval_lower_bound'])
                if 'metric_interval_upper_bound' in e:
                    step_adjustment['MetricIntervalUpperBound'] = int(e['metric_interval_upper_bound'])
                if 'scaling_adjustment' in e:
                    step_adjustment['ScalingAdjustment'] = int (e['scaling_adjustment'])
                step_adjustments.append(step_adjustment)
        else:
            step_adjustment = {}
            step_adjustment['MetricIntervalLowerBound'] = 0
            step_adjustment['ScalingAdjustment'] = 1
            step_adjustments.append(step_adjustment)
            step_adjustment = {}
            step_adjustment['MetricIntervalUpperBound'] = 0
            step_adjustment['ScalingAdjustment'] = -1
            step_adjustments.append(step_adjustment)
      
        properties['StepScalingPolicyConfiguration']['StepAdjustments'] = step_adjustments
        for i in properties['StepScalingPolicyConfiguration']['StepAdjustments']:
            if 'MetricIntervalLowerBound' in i:
                self._log_information(key = '- MetricIntervalLowerBound', value=i['MetricIntervalLowerBound'], indent=7)
            if 'MetricIntervalUpperBound' in i:
                self._log_information(key = '- MetricIntervalUpperBound', value=i['MetricIntervalUpperBound'], indent=7)
            if 'ScalingAdjustment' in i:
                self._log_information(key = 'ScalingAdjustment', value=i['ScalingAdjustment'], indent=9)
        cfn['Properties'] = properties
        self.infos.green_infos.stack['Resources'][f'AutoScalingPolicy{count_policy}'] = cfn

    def _process_cloudwatch_alarm(self, alarm, count_policy, count_cloudwatch_alarms):
        cfn = {}
        cfn['Type'] = 'AWS::CloudWatch::Alarm'
        properties = {}

        properties['MetricName'] = alarm['metric_name']
        self._log_information(key = '- MetricName', value=properties['MetricName'], indent=6)

        properties['AlarmDescription'] = f'Containers {properties["MetricName"]} High'
        if 'alarm_description' in alarm:
            properties['AlarmDescription'] = alarm['alarm_description']
        self._log_information(key = 'AlarmDescription', value=properties['AlarmDescription'], indent=8)
        
        properties['Namespace'] = 'AWS/ECS'
        if 'namespace' in alarm:
            properties['Namespace'] = alarm['namespace']
        self._log_information(key = 'Namespace', value=properties['Namespace'], indent=8)

        properties['Statistic'] = 'Average'
        if 'statistic' in alarm:
            properties['Statistic'] = alarm['statistic']
        self._log_information(key = 'Statistic', value=properties['Statistic'], indent=8)

        properties['Period'] = 300
        if 'period' in alarm:
            properties['Period'] = int(alarm['period'])

        self._log_information(key = 'Period', value=properties['Period'], indent=8)

        properties['EvaluationPeriods'] = 1
        if 'evaluation_periods' in alarm:
            properties['EvaluationPeriods'] = int(alarm['evaluation_periods'])
        self._log_information(key = 'EvaluationPeriods', value=properties['EvaluationPeriods'], indent=8)

        properties['Threshold'] = int(alarm['threshold'])
        self._log_information(key = 'Threshold', value=properties['Threshold'], indent=8)
        properties['AlarmActions'] = []
        alarm_action = {}
        alarm_action['Ref'] = f'AutoScalingPolicy{count_policy}'
        properties['AlarmActions'].append(alarm_action)
        
        dimensions = []
        if 'dimensions' in alarm:
            for item in alarms['dimensions']:
                dimension = {}
                dimension['Name'] = item['name']
                dimension['Value'] = item['Value']
                dimensions.append(dimension)
        else:
            dimension = {}
            dimension['Name'] = 'ServiceName'
            dimension['Value'] = f'{self.infos.service_name}-{self.infos.green_infos.canary_release}'
            dimensions.append(dimension)
            dimension = {}
            dimension['Name'] = 'ClusterName'
            dimension['Value'] = f'{self.infos.cluster_name}'
            dimensions.append(dimension)

        properties['Dimensions'] = dimensions
        self._log_information(key = '  Dimensions', value='', indent=6)
        for d in properties['Dimensions']:
            self._log_information(key = '- Name', value=d['Name'], indent=9)
            self._log_information(key = 'Value', value=d['Value'], indent=11)

        properties['ComparisonOperator'] = alarm['comparison_operator']
        self._log_information(key = 'ComparisonOperator', value=properties['ComparisonOperator'], indent=8)
        cfn['Properties'] = properties
        cfn['DependsOn'] = f'AutoScalingPolicy{count_policy}'
        self.infos.green_infos.stack['Resources'][f'AutoScalingAlarm{count_cloudwatch_alarms}'] = cfn

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_scheduling_strategy()
            self._process_platform_version()
            self._process_placement_constraints()
            self._process_placement_stategies()
            self._process_load_balancer()
            self._process_auto_scaling()
            self.infos.save()
            return PrepareDeploymentTaskDefinitionStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None
