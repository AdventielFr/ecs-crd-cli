
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
            self._log_information(key='Desired  Instances', value=self.infos.scale_infos.desired , ljust=18)
            self._log_information(key='Wait', value=f'{wait}s' , ljust=18)
            if 'auto_scaling_policy' in scale:
                self._log_information(key = "Auto Scaling Policy", value= None)
                auto_scaling_policy = scale['auto_scaling_policy']
                self._process_application_autoscaling_scalable_target(auto_scaling_policy)
                self._process_application_auto_scaling_scaling_policy(auto_scaling_policy)
                if 'alarms' in scale['auto_scaling_policy']:
                    self._log_information(key = 'CloudWatch Alarms', value='', indent=2)
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
        self._log_information(key = 'Application Auto Scaling (ScalableTarget)', value= None, indent=1)
        if 'minimum' in auto_scaling_policy:
            properties['MinCapacity'] = int(auto_scaling_policy['minimum'])
        else:
            properties['MinCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MinCapacity', value=properties['MinCapacity'], indent=2)
        if 'maximum' in auto_scaling_policy:
            properties['MaxCapacity'] = int(auto_scaling_policy['maximum'])
        else:
            properties['MaxCapacity'] = self.infos.scale_infos.desired
        self._log_information(key = 'MaxCapacity', value=properties['MaxCapacity'], indent=2)
        properties['ResourceId'] = f'service/{self.infos.cluster_name}/{self.infos.service_name}-{self.infos.green_infos.canary_release}'
        self._log_information(key = 'ResourceId', value=properties['ResourceId'], indent=2)
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        self._log_information(key = 'ScalableDimension', value=properties['ScalableDimension'], indent=2)
        properties['ServiceNamespace'] = 'ecs'
        self._log_information(key = 'ServiceNamespace', value=properties['ServiceNamespace'], indent=2)
        properties['RoleARN'] = self.bind_data(auto_scaling_policy['role_arn'])
        self._log_information(key = 'RoleARN', value=properties['RoleARN'], indent=2)
        cfn['Properties'] = properties
        cfn['DependsOn'] = 'Service'
        self.infos.green_infos.stack['Resources']['AutoScalingTarget'] = cfn

    def _process_application_auto_scaling_scaling_policy(self, auto_scaling_policy):
        cfn = {}
        self._log_information(key = 'Application Auto Scaling (ScalingPolicy)', value= None, indent=1)
        cfn['Type'] = 'AWS::ApplicationAutoScaling::ScalingPolicy'
        properties = {}
        properties['PolicyName'] = f'{self.infos.service_name}-scaling-policy'
        if 'policy_name' in auto_scaling_policy:
            properties['PolicyName']  = auto_scaling_policy['policy_name']
        self._log_information(key = 'PolicyName', value=properties['PolicyName'], indent=2)
        properties['PolicyType'] = 'StepScaling'
        if 'policy_type' in auto_scaling_policy:
            properties['PolicyType'] = auto_scaling_policy['policy_type']
        self._log_information(key = 'PolicyType', value=properties['PolicyType'], indent=2)
        if 'scaling_target_id' in auto_scaling_policy:
            properties['ScalingTargetId'] = auto_scaling_policy['scaling_target_id']
        else:
            properties['ScalingTargetId'] =  {}
            properties['ScalingTargetId']['Ref'] = 'AutoScalingTarget'
        
        properties['ScalableDimension'] = 'ecs:service:DesiredCount'
        if 'scalable_dimension' in auto_scaling_policy:
            properties['ScalableDimension'] = auto_scaling_policy['scalable_dimension']
        self._log_information(key = 'ScalableDimension', value=properties['ScalableDimension'], indent=2)
        properties['ServiceNamespace'] = 'ecs'

        if 'service_namespace' in auto_scaling_policy:
            properties['ServiceNamespace'] = auto_scaling_policy['service_namespace']
        self._log_information(key = 'ServiceNamespace', value=properties['ServiceNamespace'], indent=2)

        properties['StepScalingPolicyConfiguration'] = {}
        self._log_information(key = 'StepScalingPolicyConfiguration', value='', indent=2)

        properties['StepScalingPolicyConfiguration']['AdjustmentType'] = 'ChangeInCapacity'
        if  'step_scaling_policy_configuration' in auto_scaling_policy and 'adjustment_type' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['AdjustmentType'] = auto_scaling_policy['step_scaling_policy_configuration']['adjustment_type']
        self._log_information(key = 'AdjustmentType', value= properties['StepScalingPolicyConfiguration']['AdjustmentType'], indent=3)
        
        properties['StepScalingPolicyConfiguration']['Cooldown'] = 60
        if 'step_scaling_policy_configuration' in auto_scaling_policy and 'cool_down' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['Cooldown'] = int(auto_scaling_policy['step_scaling_policy_configuration']['cool_down'])
        self._log_information(key = 'Cooldown', value= properties['StepScalingPolicyConfiguration']['Cooldown'], indent=3)
        
        
        properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = 'Average'
        if 'step_scaling_policy_configuration' in auto_scaling_policy and 'metric_aggregation_type' in auto_scaling_policy['step_scaling_policy_configuration']:
            properties['StepScalingPolicyConfiguration']['MetricAggregationType'] = auto_scaling_policy['step_scaling_policy_configuration']['metric_aggregation_type']
        self._log_information(key = 'MetricAggregationType', value= properties['StepScalingPolicyConfiguration']['MetricAggregationType'], indent=3)

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

        
        for i in properties['StepScalingPolicyConfiguration']['StepAdjustments']:
            if 'MetricIntervalLowerBound' in i:
                self._log_information(key = '- MetricIntervalLowerBound', value=i['MetricIntervalLowerBound'], indent=3)
            if 'MetricIntervalUpperBound' in i:
                self._log_information(key = '- MetricIntervalUpperBound', value=i['MetricIntervalUpperBound'], indent=3)
            if 'ScalingAdjustment' in i:
                self._log_information(key = '  ScalingAdjustment', value=i['ScalingAdjustment'], indent=3)
        cfn['Properties'] = properties
        self.infos.green_infos.stack['Resources']['AutoScalingPolicy'] = cfn

    def _process_cloudwatch_alarm(self, alarm, count):
        cfn = {}
        cfn['Type'] = 'AWS::CloudWatch::Alarm'
        properties = {}

        properties['MetricName'] = alarm['metric_name']
        self._log_information(key = '- MetricName', value=properties['MetricName'], indent=3)

        properties['AlarmDescription'] = f'Containers {properties["MetricName"]} High'
        if 'alarm_description' in alarm:
            properties['AlarmDescription'] = alarm['alarm_description']
        self._log_information(key = '  AlarmDescription', value=properties['AlarmDescription'], indent=3)
        
        properties['Namespace'] = 'AWS/ECS'
        if 'namespace' in alarm:
            properties['Namespace'] = alarm['namespace']
        self._log_information(key = '  Namespace', value=properties['Namespace'], indent=3)

        properties['Statistic'] = 'Average'
        if 'statistic' in alarm:
            properties['Statistic'] = alarm['statistic']
        self._log_information(key = '  Statistic', value=properties['Statistic'], indent=3)

        properties['Period'] = 300
        if 'period' in alarm:
            properties['Period'] = int(alarm['period'])

        self._log_information(key = '  Period', value=properties['Period'], indent=3)

        properties['EvaluationPeriods'] = 1
        if 'evaluation_periods' in alarm:
            properties['EvaluationPeriods'] = int(alarm['evaluation_periods'])
        self._log_information(key = '  EvaluationPeriods', value=properties['EvaluationPeriods'], indent=3)

        properties['Threshold'] = int(alarm['threshold'])
        self._log_information(key = '  Threshold', value=properties['Threshold'], indent=3)
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
