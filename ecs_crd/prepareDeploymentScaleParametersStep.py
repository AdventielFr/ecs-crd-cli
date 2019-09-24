
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.prepareDeploymentContainerDefinitionsStep import PrepareDeploymentContainerDefinitionsStep

class PrepareDeploymentScaleParametersStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Scale parameters )', logger)
        self.min_wait = 40

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            desired = 2
            wait = self.min_wait 
            self.infos.scale_infos = ScaleInfos()
            if 'scale' in self.configuration['canary']:
                scale = self.configuration['canary']['scale']
                if 'desired' in scale:
                    self.infos.scale_infos.desired = int(scale['desired'])
                if 'wait' in scale:
                    self.infos.scale_infos.wait = int(scale['wait'])
                if 'minimum' in scale:
                    self.infos.scale_infos.minimum = int(scale['minimum'])
                else:
                    self.infos.scale_infos.minimum = self.infos.scale_infos.desired
                if 'maximum' in scale:
                    self.infos.scale_infos.maximum = int(scale['maximum'])
                else:
                    self.infos.scale_infos.maximum = self.infos.scale_infos.desired
            self._log_information(key='Desired  Instances', value=self.infos.scale_infos.desired , ljust=18)
            self._log_information(key='Minimum  Instances', value=self.infos.scale_infos.minimum , ljust=18)
            self._log_information(key='Maximum  Instances', value=self.infos.scale_infos.maximum , ljust=18)
            self._log_information(key='Wait', value=f'{wait}s' , ljust=18)
            if 'auto_scaling_policy' in scale:
                auto_scaling_policy = scale['auto_scaling_policy']
                self._process_application_autoscaling_scalable_target(auto_scaling_policy)
                self._process_application_auto_scaling_scaling_policy(auto_scaling_policy)
                if 'alarms' in scale['auto_scaling_policy']:
                    count = 1
                    for alarm in scale['auto_scaling_policy']['alarms']:
                        self._process_cloudwatch_alarm(alarm, count)
                        count = count + 1
           
            self.infos.save()
            
            return PrepareDeploymentContainerDefinitionsStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

    def _process_application_autoscaling_scalable_target(self, auto_scaling_policy):
        cfn = {}
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalableTarget'
        properties = {}
        properties['MaxCapacity'] = self.infos.scale_infos.maximum
        properties['MinCapacity'] = self.infos.scale_infos.minimum
        properties['ResourceId'] = f'service/{self.infos.cluster_name}/{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        properties['ServiceNamespace'] = 'ecs'
        properties['RoleARN'] = self.bind_data(auto_scaling_policy['role_arn'])
        cfn['Properties'] = properties
        cfn['DependsOn'] = 'Service'
        self.infos.green_infos.stack['Resources']['AutoScalingTarget'] = cfn

    def _process_application_auto_scaling_scaling_policy(self, auto_scaling_policy):
        cfn = {}
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalingPolicy'
        properties = {}
        properties['PolicyName'] = f'{self.infos.service_name}-scaling-policy'
        if 'policy_name' in auto_scaling_policy:
            properties['PolicyName']  = auto_scaling_policy['policy_name']

        properties['PolicyType'] = 'StepScaling'
        if 'policy_type' in auto_scaling_policy:
            properties['PolicyType'] = auto_scaling_policy['policy_type']

        if 'scaling_target_id' in auto_scaling_policy:
            properties['ScalingTargetId'] = auto_scaling_policy['scaling_target_id']
        else:
            properties['ScalingTargetId'] =  {}
            properties['ScalingTargetId']['Ref'] = 'AutoScalingTarget'
        
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        if 'scalable_dimension' in auto_scaling_policy:
            properties['ScalableDimension'] = auto_scaling_policy['scalable_dimension']
         
        properties['ServiceNamespace'] = 'ecs'
        if 'service_namespace' in auto_scaling_policy:
            properties['ServiceNamespace'] = auto_scaling_policy['service_namespace']

        properties['StepScalingPolicyConfiguration'] = {}

        properties['StepScalingPolicyConfiguration']['AdjustmentType'] = 'ChangeInCapacity'
        if  'step_scaling_policy_configuration' in auto_scaling_policy and 'adjustment_type' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['AdjustmentType'] = auto_scaling_policy['step_scaling_policy_configuration']['adjustment_type']
        
        properties['StepScalingPolicyConfiguration']['Cooldown'] = 60
        if 'step_scaling_policy_configuration' in auto_scaling_policy and 'cool_down' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['Cooldown'] = int(auto_scaling_policy['step_scaling_policy_configuration']['cool_down'])
        
        properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = 'Average'
        if 'step_scaling_policy_configuration' in auto_scaling_policy and 'metric_aggregation_type' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = auto_scaling_policy['step_scaling_policy_configuration']['metric_aggregation_type']

        properties['StepScalingPolicyConfiguration']['StepAdjustments'] = []
        step_adjustments = []
        if 'step_scaling_policy_configuration' in auto_scaling_policy and 'step_adjustments' in auto_scaling_policy['step_scaling_policy_configuration']:
            for e in auto_scaling_policy['step_scaling_policy_configuration']['step_adjustments']:
                step_adjustment = {}
                if 'metric_interval_lower_bound' in e:
                    step_adjustment['MetricIntervalLowerBound'] = int(auto_scaling_policy['metric_interval_lower_bound'])
                if 'metric_interval_upper_bound' in e:
                    step_adjustment['MetricIntervalUpperBound'] = int(auto_scaling_policy['metric_interval_upper_bound'])
                if 'scaling_adjustment' in e:
                    step_adjustment['ScalingAdjustment'] = int (auto_scaling_policy['scaling_adjustment'])
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
        cfn['Properties'] = properties
        self.infos.green_infos.stack['Resources']['AutoScalingPolicy'] = cfn

    def _process_cloudwatch_alarm(self, alarm, count):
        cfn = {}
        cfn['Type'] = 'AWS::CloudWatch::Alarm'
        properties = {}

        properties['MetricName'] = alarm['metric_name']
        
        properties['AlarmDescription'] = f'Containers {properties["MetricName"]} High'
        if 'alarm_description' in alarm:
            properties['AlarmDescription'] = alarm['alarm_description']
        
        properties['Namespace'] = 'AWS/ECS'
        if 'namespace' in alarm:
            properties['Namespace'] = alarm['namespace']
       
        properties['Statistic'] = 'Average'
        if 'statistic' in alarm:
            properties['Statistic'] = alarm['statistic']

        properties['Period'] = 300
        if 'period' in alarm:
            properties['Period'] = int(alarm['period'])

        properties['EvaluationPeriods'] = 1
        if 'evaluation_periods' in alarm:
            properties['EvaluationPeriods'] = int(alarm['evaluation_periods'])

        properties['Threshold'] = int(alarm['threshold'])
        properties['AlarmActions'] = []
        alarm_action = {}
        alarm_action['Ref'] = 'AutoScalingPolicy'
        properties['AlarmActions'].append(alarm_action)
        properties['Dimensions'] = []
        dimension = {}
        dimension['Name'] = 'ServiceName'
        dimension['Value'] = f'{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        properties['Dimensions'].append(dimension)
        dimension = {}
        dimension['Name'] = 'ClusterName'
        dimension['Value'] = f'{self.infos.cluster_name}'
        properties['Dimensions'].append(dimension)
        properties['ComparisonOperator'] = 'GreaterThanOrEqualToThreshold'
        cfn['Properties'] = properties
        cfn['DependsOn'] = 'AutoScalingPolicy'
        self.infos.green_infos.stack['Resources'][f'AutoScalingAlarm{count}'] = cfn
