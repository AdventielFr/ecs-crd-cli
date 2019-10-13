#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTaskDefinitionStep import PrepareDeploymentTaskDefinitionStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentServiceDefinitionStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Service definition )', logger)

    def _process_scheduling_strategy(self, source, target):
        """update the sceduling stratégy informations for the service"""
        self._process_property(
            source = source,
            target = target,
            pattern= 'DAEMON|REPLICA',
            source_property = 'scheduling_strategy',
            parent_property = 'Service',
            indent = 1
        )
    
    def _process_platform_version(self, source, target):
        """update the plaform version informations for the service"""
        self._process_property(
            source = source,
            target = target,
            source_property = 'platform_version',
            parent_property = 'Service',
            indent = 1
        )
  
    def _process_placement_constraints(self, source, target):
        """update the placement constraintes informations for the service"""
        if 'placement_constraints' in source:
            self._log_information(key='Placement Contraints', value='',indent=1)
            placement_constraints = []
            for item in source['placement_constraints']:
                constraint = {}
                self._process_placement_constraints_contraint_type(item, constraint)
                self._process_placement_constraints_contraint_expression(item, constraint)
                placement_constraints.append(constraint)
            target['PlacementConstraints'] = placement_constraints

    def _process_placement_constraints_contraint_type(self, source, target):
        self._process_property(
            source = source,
            target = target,
            pattern= 'distinctInstance|memberOf',
            multi = True,
            required = True,
            source_property = 'type',
            parent_property = 'Service.PlacementConstraints.Type',
            indent = 2
        )

    def _process_placement_constraints_contraint_expression(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'expression',
            parent_property = 'Service.PlacementConstraints.Expression',
            indent = 4
        )
    
    def _process_placement_stategies(self, source, properties):
        """update the placement strategies informations for the service"""
        if 'placement_strategies' in source:
            self._log_information(key='Placement Strategies',value='', ljust=10, indent=1)
            placement_stategies = []
            for item in source['placement_strategies']:
                strategy = {}
                self._process_placement_stategies_strategy_type(item, strategy)
                self._process_placement_stategies_strategy_field(item,strategy)
                placement_stategies.append(strategy)
            properties['PlacementStrategies'] = placement_stategies
    
    def _process_placement_stategies_strategy_field(self,source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'field',
            required = True,
            multi = False,
            parent_property = 'Service.PlacementStrategies',
            indent = 4
        )

    def _process_placement_stategies_strategy_type(self,source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'type',
            required = True,
            pattern = 'binpack|random|spread',
            multi = True,
            parent_property = 'Service.PlacementStrategies',
            indent = 2
        )

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

    def _process_auto_scaling(self, source):            
        if 'auto_scaling' in source:
            self._log_information(key = "AutoScaling", value='', indent=1)
            source = source['auto_scaling']
            self._process_application_autoscaling_scalable_target(source)
            count = 1
            for item in source['auto_scaling_policies']:
                self._process_application_auto_scaling_scaling_policy(item, count)

    def _process_application_autoscaling_scalable_target_min_capacity(self, source, target):
       self._process_property(
            source = source,
            target = target,
            source_property = 'min_capacity',
            type = int,
            default = self.infos.scale_infos.desired,
            parent_property = 'Service.AutoScaling',
            indent = 2
        )

    def _process_application_autoscaling_scalable_target_max_capacity(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'max_capacity',
            type = int,
            default = self.infos.scale_infos.desired,
            parent_property = 'Service.AutoScaling',
            indent = 2
        )

    def _process_application_autoscaling_scalable_target_role_arn(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'role_arn',
            target_property = 'RoleARN',
            required = True,
            parent_property = 'Service.AutoScaling',
            indent = 2
        )

    def _process_application_autoscaling_scalable_target(self, source):
        cfn = {}
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalableTarget'
        target = {}
        # min_capacity
        self._process_application_autoscaling_scalable_target_min_capacity(source, target)
        # max_capacity
        self._process_application_autoscaling_scalable_target_max_capacity(source, target)
        # role_arn
        self._process_application_autoscaling_scalable_target_role_arn(source, target)
        target['ResourceId'] = f'service/{self.infos.cluster_name}/{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        target['ScalableDimension'] = 'ecs:service:DesiredCount'
        target['ServiceNamespace'] = 'ecs'
        cfn['Properties'] = target
        cfn['DependsOn'] = 'Service'
        self.infos.green_infos.stack['Resources']['AutoScalingTarget'] = cfn

    def _process_application_auto_scaling_scaling_policy_policy_name(self, source, target, count):
        self._process_property(
            source = source,
            target = target,
            source_property = 'policy_name',
            multi = True,
            parent_property = 'Service.AutoScaling',
            default = f'{self.infos.service_name}-scaling-policy-{count}',
            indent = 3
        )

    def _process_application_auto_scaling_scaling_policy_policy_type(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'policy_type',
            pattern ='SimpleScaling|StepScaling|TargetTrackingScaling',
            parent_property = 'Service.AutoScaling',
            default = 'StepScaling',
            indent = 5
        )

    def _process_application_auto_scaling_scaling_policy(self, source, count):
        cfn = {}
        self._log_information(key = 'AutoScalingPolicies', value= '', indent=2)
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalingPolicy'
        target = {}
        # policy_name
        self._process_application_auto_scaling_scaling_policy_policy_name(source, target, count)
        # policy_type
        self._process_application_auto_scaling_scaling_policy_policy_type(source, target)
        target['ScalingTargetId'] =  {}
        target['ScalingTargetId']['Ref'] = 'AutoScalingTarget'
        target['ScalableDimension'] = 'ecs:service:DesiredCount'
        target['ServiceNamespace'] = 'ecs'
        
        self._process_step_scaling_policy_configuration(source, target)
        self._process_cloudwatch_alarms(source, target, count)
        cfn['Properties'] = target
        self.infos.green_infos.stack['Resources'][f'AutoScalingPolicy{count}'] = cfn

    def _process_step_scaling_policy_configuration_adjustment_type(self, source, target):
        """process step_scaling_policy_configuration.adjustment_type"""
        self._process_property(
            source = source,
            target = target,
            source_property = 'adjustment_type',
            pattern = 'ChangeInCapacity|ExactCapacity|PercentChangeInCapacity',
            default = 'ChangeInCapacity',
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 6
        )
       
    def _process_step_scaling_policy_configuration_cooldown(self, source, target):
        """process step_scaling_policy_configuration.cooldown"""
        self._process_property(
            source = source,
            target = target,
            source_property = 'cooldown',
            type = int,
            default = 60,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 6
        )
   
    def _process_step_scaling_policy_configuration_metric_aggregation_type(self, source, target):
        """process step_scaling_policy_configuration.metric_aggregation_type"""
        self._process_property(
            source = source,
            target = target,
            source_property = 'metric_aggregation_type',
            pattern = 'Average|Minimum|Maximum',
            default = 'Average',
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 6
        )
      
    def _process_step_scaling_policy_configuration(self, source, target):
        if 'step_scaling_policy_configuration' not in source:
            raise ValueError('The StepScalingPolicyConfiguration is required')
        sub_source = source['step_scaling_policy_configuration']   
        sub_target = {}
        self._log_information(key = 'StepScalingPolicyConfiguration', value='', indent=5)
        # adjustment_type
        self._process_step_scaling_policy_configuration_adjustment_type(sub_source, sub_target)

        # cooldown
        self._process_step_scaling_policy_configuration_cooldown(sub_source,sub_target)
        # metric_aggregation_type
        self._process_step_scaling_policy_configuration_metric_aggregation_type(sub_source, sub_target)
        # step_adjustments
        self._process_step_scaling_policy_configuration_step_adjustments(sub_source, sub_target)
        target['StepScalingPolicyConfiguration'] = sub_target

    def _process_step_scaling_policy_configuration_step_adjustments(self, source, target):
        if 'step_adjustments' not in source:
            raise ValueError('StepAdjustments is required')
        target['StepAdjustments'] = []
        self._log_information(key='StepAdjustments',value ='',indent=6)
        for sub_source in source['step_adjustments']:
                sub_target = {}
                # metric_interval_lower_bound
                self._process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(sub_source, sub_target)
                # metric_interval_upper_bound
                self._process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(sub_source, sub_target)
                # scaling_adjustment
                self._process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(sub_source, sub_target)
                target['StepAdjustments'].append(sub_target)
   
    def _process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'metric_interval_lower_bound',
            type = int,
            multi = True,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.StepAdjustment',
            indent = 7
        )

    def _process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'metric_interval_upper_bound',
            type = int,
            multi = True,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.StepAdjustment',
            indent = 7
        )

    def _process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'scaling_adjustment',
            type = int,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.StepAdjustment',
            indent = 9
        )

    def _process_cloudwatch_alarms(self, source, target, count):
        if 'cloudwatch_alarms' not in source:
            raise ValueError('CloudwatchAlarms is required for Service.AutoScaling.StepScalingPolicyConfiguration.')
        self._log_information(key='CloudWatch Alarms', value='', indent=5)
        count_cloudwatch_alarms = 1
        for sub_source in source['cloudwatch_alarms']:
            self._process_cloudwatch_alarm(sub_source, count, count_cloudwatch_alarms)
            count_cloudwatch_alarms = count_cloudwatch_alarms + 1

    def _process_cloudwatch_alarm_metric_name(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'metric_name',
            pattern = 'CPUUtilization|MemoryUtilization',
            default = 'Average',
            multi = True,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.CloudwatchAlarms',
            indent = 6
        )

    def _process_cloudwatch_alarm_alarm_description(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'alarm_description',
            default = f'Containers {target["MetricName"]} High',
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.CloudwatchAlarms',
            indent = 8
        )

    def _process_cloudwatch_alarm_namespace(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'namespace',
            default = 'AWS/ECS',
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration.CloudwatchAlarms',
            indent = 8
        )

    def _process_cloudwatch_alarm_statistic(self, source, target):
        self._process_property(
            source = source,
            target = target,
            source_property = 'statistic',
            pattern = 'Average|Maximum|Minimum|SampleCount|Sum',
            default = 'Average',
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 8
        )
    
    def _process_cloudwatch_alarm_period(self, source, target):
       self._process_property(
            source = source,
            target = target,
            source_property = 'period',
            type = int,
            default = 300,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 8
        )

    def _process_cloudwatch_alarm_evaluation_periods(self, source, target):
       self._process_property(
            source = source,
            target = target,
            source_property = 'evaluation_periods',
            type = int,
            default = 1,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 8
        )
 
    def _process_cloudwatch_alarm_threshold(self, source, target):
       self._process_property(
            source = source,
            target = target,
            source_property = 'threshold',
            type = int,
            required = True,
            parent_property = 'Service.AutoScaling.StepScalingPolicyConfiguration',
            indent = 8
        )

    def _process_cloudwatch_alarm_comparison_operator(self, origin, target):
        if 'comparison_operator' in origin:
            val = re.match('GreaterThanOrEqualToThreshold|GreaterThanThreshold|LessThanOrEqualToThreshold|LessThanThreshold', origin['comparison_operator'])
            if not val:
                raise ValueError(f'{origin["comparison_operator"]} is not valid for CloudwatchAlarm.ComparisonOperator.')
            target['ComparisonOperator'] = val.group(0)
        else:
           raise ValueError('ComparisonOperator is required in CloudwatchAlarm')
        self._log_information(key = 'ComparisonOperator', value=target['ComparisonOperator'], indent=8)

    def _process_cloudwatch_alarm(self, origin, count_policy, count_cloudwatch_alarms):
        cfn = {}
        cfn['Type'] = 'AWS::CloudWatch::Alarm'
        target = {}
        # metric_name
        self._process_cloudwatch_alarm_metric_name(origin, target)
        # alarm_description
        self._process_cloudwatch_alarm_alarm_description(origin, target)
        # namespace
        self._process_cloudwatch_alarm_namespace(origin, target)
        # statistic
        self._process_cloudwatch_alarm_statistic(origin, target)
        # period
        self._process_cloudwatch_alarm_period(origin, target)
        # evaluation_periods
        self._process_cloudwatch_alarm_evaluation_periods(origin, target)
        # threshold
        self._process_cloudwatch_alarm_threshold(origin, target)
        # comparison_operator
        self._process_cloudwatch_alarm_comparison_operator(origin, target)

        target['AlarmActions'] = []
        alarm_action = {}
        alarm_action['Ref'] = f'AutoScalingPolicy{count_policy}'
        target['AlarmActions'].append(alarm_action)

        dimensions = []
        dimension = {}
        dimension['Name'] = 'ServiceName'
        dimension['Value'] = f'{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        dimensions.append(dimension)
        dimension = {}
        dimension['Name'] = 'ClusterName'
        dimension['Value'] = f'{self.infos.cluster_name}'
        dimensions.append(dimension)
        target['Dimensions'] = dimensions

        self._log_information(key = '  Dimensions', value='', indent=6)
        for d in target['Dimensions']:
            self._log_information(key = '- Name', value=d['Name'], indent=9)
            self._log_information(key = 'Value', value=d['Value'], indent=11)
        cfn['Properties'] = target
        cfn['DependsOn'] = f'AutoScalingPolicy{count_policy}'
        self.infos.green_infos.stack['Resources'][f'AutoScalingAlarm{count_cloudwatch_alarms}'] = cfn

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            source = self.configuration['service']
            target = self.infos.green_infos.stack['Resources']['Service']['Properties']

            self._process_scheduling_strategy(source, target)
            self._process_platform_version(source, target)
            self._process_placement_constraints(source, target)
            self._process_placement_stategies(source, target)
            self._process_load_balancer()
            self._process_auto_scaling(source)
            self.infos.save()
            return PrepareDeploymentTaskDefinitionStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 5
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)
