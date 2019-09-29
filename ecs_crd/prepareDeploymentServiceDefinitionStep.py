#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTaskDefinitionStep import PrepareDeploymentTaskDefinitionStep

class PrepareDeploymentServiceDefinitionStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Service definition )', logger)

    def process_scheduling_strategy(self, origin, properties):
        """update the sceduling stratégy informations for the service"""
        if 'scheduling_strategy' in origin:
            val = re.match('DAEMON|REPLICA', origin['scheduling_strategy'])
            if not val:
                raise ValueError(f'{origin["scheduling_strategy"]} is not valid for SchedulingStrategy.')
            properties['SchedulingStrategy'] = val.group(0)
        else:
            properties['SchedulingStrategy'] = 'REPLICA'
        self._log_information(key='Scheduling Strategy', value=properties['SchedulingStrategy'], ljust=10, indent=1)
    
    def process_platform_version(self, origin, properties):
        """update the plaform version informations for the service"""
        if 'platform_version' in origin:
            properties['PlatformVersion'] = origin['platform_version']
            self._log_information(key='Platform Version', value=origin['PlatformVersion'], ljust=10, indent=1)

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

    def process_auto_scaling(self, origin):            
        if 'auto_scaling' in origin:
            self._log_information(key = "AutoScaling", value='', indent=1)
            origin = origin['auto_scaling']
            self.process_application_autoscaling_scalable_target(origin)
            count = 1
            for item in origin['auto_scaling_policies']:
                self.process_application_auto_scaling_scaling_policy(item, count)

    def process_application_autoscaling_scalable_target(self, origin):
        cfn = {}
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalableTarget'
        properties = {}
        if 'min_capacity' in origin:
            properties['MinCapacity'] = int(origin['min_capacity'])
        else:
            properties['MinCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MinCapacity', value=properties['MinCapacity'], indent=2)
        if 'max_capacity' in origin:
            properties['MaxCapacity'] = int(origin['max_capacity'])
        else:
            properties['MaxCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MaxCapacity', value=properties['MaxCapacity'], indent=2)
        
        properties['ResourceId'] = f'service/{self.infos.cluster_name}/{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        properties['ServiceNamespace'] = 'ecs'
        properties['RoleARN'] = self.bind_data(origin['role_arn'])
        self._log_information(key = 'RoleARN', value=properties['RoleARN'], indent=2)

        cfn['Properties'] = properties
        cfn['DependsOn'] = 'Service'
        self.infos.green_infos.stack['Resources']['AutoScalingTarget'] = cfn

    def process_application_auto_scaling_scaling_policy(self, origin, count):
        cfn = {}
        self._log_information(key = 'AutoScalingPolicies', value= '', indent=2)
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalingPolicy'
        properties = {}
        properties['PolicyName'] = f'{self.infos.service_name}-scaling-policy-{count}'
        if 'policy_name' in origin:
            properties['PolicyName']  = origin['policy_name']
        self._log_information(key = '- PolicyName', value=properties['PolicyName'], indent=3)
        properties['PolicyType'] = 'StepScaling'
        self._log_information(key = 'PolicyType', value=properties['PolicyType'], indent=5)
        properties['ScalingTargetId'] =  {}
        properties['ScalingTargetId']['Ref'] = 'AutoScalingTarget'
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        properties['ServiceNamespace'] = 'ecs'
        self.process_step_scaling_policy_configuration(origin, properties)
        self.process_cloudwatch_alarms(origin, properties, count)
        cfn['Properties'] = properties
        self.infos.green_infos.stack['Resources'][f'AutoScalingPolicy{count}'] = cfn

    def process_step_scaling_policy_configuration_adjustment_type(self, source, properties):
        """process step_scaling_policy_configuration.adjustment_type"""
        if 'adjustment_type' in source:
            val = re.match('ChangeInCapacity|ExactCapacity|PercentChangeInCapacity', source['adjustment_type'])
            if not val:
                raise ValueError(f'{source["adjustment_type"]} is not valid for StepScalingPolicyConfiguration.')
            properties['AdjustmentType'] = val.group(0)
        else:
            properties['AdjustmentType'] = 'ChangeInCapacity'
        self._log_information(key = 'AdjustmentType', value=properties['AdjustmentType'], indent=6)
    
    def process_step_scaling_policy_configuration_cooldown(self, source, properties):
        """process step_scaling_policy_configuration.cooldown"""
        if 'cooldown' in source:
            if not isinstance(source['cooldown'], int) or source['cooldown'] < 0:
                raise ValueError(f'{source["cooldown"]} is not valid for StepScalingPolicyConfiguration.')
            properties['Cooldown'] = int(source['cooldown'])
        else:
            properties['Cooldown'] = 60
        self._log_information(key = 'Cooldown', value=properties['Cooldown'], indent=6)
   
    def process_step_scaling_policy_configuration_metric_aggregation_type(self, source, properties):
        """process step_scaling_policy_configuration.metric_aggregation_type"""
        if 'metric_aggregation_type' in source:
            val = re.match('Average|Minimum|Maximum', source['metric_aggregation_type'])
            if not val:
                raise ValueError(f'{source["metric_aggregation_type"]} is not valid for StepScalingPolicyConfiguration.')
            properties['MetricAggregationType'] = val.group(0)
        else:
            properties['MetricAggregationType'] = 'Average'
        self._log_information(key = 'MetricAggregationType', value=properties['MetricAggregationType'], indent=6)

    def process_step_scaling_policy_configuration(self, origin, target):
        if 'step_scaling_policy_configuration' not in origin:
            raise ValueError('The StepScalingPolicyConfiguration is required')
        sub_origin= origin['step_scaling_policy_configuration']   
        sub_target = {}
        self._log_information(key = 'StepScalingPolicyConfiguration', value='', indent=5)
        # adjustment_type
        self.process_step_scaling_policy_configuration_adjustment_type(sub_origin, sub_target)
        # cooldown
        self.process_step_scaling_policy_configuration_cooldown(sub_origin,sub_target)
        # metric_aggregation_type
        self.process_step_scaling_policy_configuration_metric_aggregation_type(sub_origin, sub_target)
        # step_adjustments
        self.process_step_scaling_policy_configuration_step_adjustments(sub_origin, sub_target)
        target['StepScalingPolicyConfiguration'] = sub_target

    def process_step_scaling_policy_configuration_step_adjustments(self, origin, target):
        if 'step_adjustments' not in origin:
            raise ValueError('StepAdjustments is required')
        target['StepAdjustments'] = [] 
        for sub_origin in origin['step_adjustments']:
                sub_target = {}
                # metric_interval_lower_bound
                self.process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(sub_origin, sub_target)
                # metric_interval_upper_bound
                self.process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(sub_origin, sub_target)
                # scaling_adjustment
                self.process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(sub_origin, sub_target)
                target['StepAdjustments'].append(sub_target)
   
    def process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(self, origin, target):
        if 'metric_interval_lower_bound' in origin:
            if not isinstance(origin['metric_interval_lower_bound'], int) :
                raise ValueError(f'{origin["metric_interval_lower_bound"]} is not valid for StepAdjustment.MetricIntervalLowerBound')
            target['MetricIntervalLowerBound'] = int(origin['metric_interval_lower_bound'])
            self._log_information(key = '- MetricIntervalLowerBound', value=target['MetricIntervalLowerBound'], indent=7)

    def process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(self, origin, target):
        if 'metric_interval_upper_bound' in origin:
            if not isinstance(origin['metric_interval_upper_bound'], int) :
                raise ValueError(f'{origin["metric_interval_upper_bound"]} is not valid for StepAdjustment.MetricIntervalUpperBound')
            target['MetricIntervalUpperBound'] = int(origin['metric_interval_upper_bound'])
            self._log_information(key = '- MetricIntervalUpperBound', value=target['MetricIntervalUpperBound'], indent=7)

    def process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(self, origin, target):
        if 'scaling_adjustment' in origin:
            if not isinstance(origin['scaling_adjustment'], int) :
                raise ValueError(f'{origin["scaling_adjustment"]} is not valid for StepAdjustment.ScalingAdjustment')
            target['ScalingAdjustment'] = int(origin['scaling_adjustment'])
            self._log_information(key = 'ScalingAdjustment', value=target['ScalingAdjustment'], indent=9)

    def process_cloudwatch_alarms(self, origin, target, count):
        if 'cloudwatch_alarms' not in origin:
            raise ValueError('CloudwatchAlarms is required')
        self._log_information(key='CloudWatch Alarms', value='', indent=5)
        count_cloudwatch_alarms = 1
        for sub_origin in origin['cloudwatch_alarms']:
            self.process_cloudwatch_alarm(sub_origin, count, count_cloudwatch_alarms)
            count_cloudwatch_alarms = count_cloudwatch_alarms + 1

    def process_cloudwatch_alarm_metric_name(self, origin, target):
        if 'metric_name' in origin:
            val = re.match('CPUUtilization|MemoryUtilization', origin['metric_name'])
            if not val:
                raise ValueError(f'{origin["metric_name"]} is not valid for CloudwatchAlarm.MetricName.')
            target['MetricName'] = val.group(0)
        else:
            raise ValueError('The MetricName is required for CloudwatchAlarm.')  
        self._log_information(key = '- MetricName', value=target['MetricName'], indent=6)  

    def process_cloudwatch_alarm_alarm_description(self, origin, target):
        if 'alarm_description' in origin:
            target['AlarmDescription'] = origin['alarm_description']
        else:
            target['AlarmDescription'] = f'Containers {target["MetricName"]} High'
        self._log_information(key = 'AlarmDescription', value=target['AlarmDescription'], indent=8)

    def process_cloudwatch_alarm_namespace(self, origin, target):
        if 'namespace' in origin:
            target['Namespace'] = origin['namespace']
        else:
            target['Namespace'] = 'AWS/ECS'
        self._log_information(key = 'Namespace', value=target['Namespace'], indent=8)
    
    def process_cloudwatch_alarm_statistic(self, origin, target):
        if 'statistic' in origin:
            val = re.match('Average|Maximum|Minimum|SampleCount|Sum', origin['statistic'])
            if not val:
                raise ValueError(f'{origin["statistic"]} is not valid for CloudwatchAlarm.Statistic.')
            target['Statistic'] = val.group(0)
        else:
            target['Statistic'] = 'Average'
        self._log_information(key = 'Statistic', value=target['Statistic'], indent=8)
    
    def process_cloudwatch_alarm_period(self, origin, target):
        if 'period' in origin:
            if not isinstance(origin['period'], int):
                raise ValueError(f'{origin["period"]} is not valid for CloudwatchAlarm.Period.')
            target['Period'] = int(origin['period'])
        else:
            target['Period'] = 300
        self._log_information(key = 'Period', value=target['Period'], indent=8)

    def process_cloudwatch_alarm_evaluation_periods(self, origin, target):
        if 'evaluation_periods' in origin:
            if not isinstance(origin['evaluation_periods'], int):
                raise ValueError(f'{origin["evaluation_periods"]} is not valid for CloudwatchAlarm.EvaluationPeriods.')
            target['EvaluationPeriods'] = int(origin['evaluation_periods'])
        else:
            target['EvaluationPeriods'] = 1
        self._log_information(key = 'EvaluationPeriods', value=target['EvaluationPeriods'], indent=8)

    def process_cloudwatch_alarm_threshold(self, origin, target):
        if 'threshold' in origin:
            if not isinstance(origin['threshold'], int):
                raise ValueError(f'{origin["threshold"]} is not valid for CloudwatchAlarm.Threshold.')
            target['Threshold'] = int(origin['threshold'])
        else:
            raise ValueError('Threshold is required in CloudwatchAlarm')
        self._log_information(key = 'Threshold', value=target['Threshold'], indent=8)

    def process_cloudwatch_alarm_comparison_operator(self, origin, target):
        if 'comparison_operator' in origin:
            val = re.match('GreaterThanOrEqualToThreshold|GreaterThanThreshold|LessThanOrEqualToThreshold|LessThanThreshold', origin['comparison_operator'])
            if not val:
                raise ValueError(f'{origin["comparison_operator"]} is not valid for CloudwatchAlarm.ComparisonOperator.')
            target['ComparisonOperator'] = val.group(0)
        else:
           raise ValueError('ComparisonOperator is required in CloudwatchAlarm')
        self._log_information(key = 'ComparisonOperator', value=target['ComparisonOperator'], indent=8)

    def process_cloudwatch_alarm(self, origin, count_policy, count_cloudwatch_alarms):
        cfn = {}
        cfn['Type'] = 'AWS::CloudWatch::Alarm'
        properties = {}
        # metric_name
        self.process_cloudwatch_alarm_metric_name(origin, properties)
        # alarm_description
        self.process_cloudwatch_alarm_alarm_description(origin, properties)
        # namespace
        self.process_cloudwatch_alarm_namespace(origin, properties)
        # statistic
        self.process_cloudwatch_alarm_statistic(origin, properties)
        # period
        self.process_cloudwatch_alarm_period(origin, properties)
        # evaluation_periods
        self.process_cloudwatch_alarm_evaluation_periods(origin, properties)
        # threshold
        self.process_cloudwatch_alarm_threshold(origin, properties)
        # comparison_operator
        self.process_cloudwatch_alarm_comparison_operator(origin, properties)

        properties['AlarmActions'] = []
        alarm_action = {}
        alarm_action['Ref'] = f'AutoScalingPolicy{count_policy}'
        properties['AlarmActions'].append(alarm_action)
        dimensions = []
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
        cfn['Properties'] = properties
        cfn['DependsOn'] = f'AutoScalingPolicy{count_policy}'
        self.infos.green_infos.stack['Resources'][f'AutoScalingAlarm{count_cloudwatch_alarms}'] = cfn

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            origin = self.configuration['service']
            properties = self.infos.green_infos.stack['Resources']['Service']['Properties']

            self.process_scheduling_strategy(origin, properties)
            self.process_platform_version(origin, properties)
            self._process_placement_constraints()
            self._process_placement_stategies()
            self._process_load_balancer()
            self.process_auto_scaling(origin)
            self.infos.save()
            return PrepareDeploymentTaskDefinitionStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None
