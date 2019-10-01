import pytest
from unittest.mock import MagicMock
import logging

from ecs_crd.canaryReleaseInfos import CanaryReleaseInfos
from ecs_crd.prepareDeploymentServiceDefinitionStep import PrepareDeploymentServiceDefinitionStep
from ecs_crd.canaryReleaseInfos import ScaleInfos

logger = logging.Logger('mock')
infos = CanaryReleaseInfos(action='test')
step = PrepareDeploymentServiceDefinitionStep(infos, logger)

def test_process_step_scaling_policy_configuration_adjustment_type_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['adjustment_type']='a'
        target = {}
        step._process_step_scaling_policy_configuration_adjustment_type(source, target)

def test_process_step_scaling_policy_configuration_adjustment_type_valid():
    source = {}
    source['adjustment_type']='ChangeInCapacity'
    target = {}
    step._process_step_scaling_policy_configuration_adjustment_type(source, target)
    assert target['AdjustmentType'] == source['adjustment_type']

    source['adjustment_type']='PercentChangeInCapacity'
    target = {}
    step._process_step_scaling_policy_configuration_adjustment_type(source, target)
    assert target['AdjustmentType'] == source['adjustment_type']

    source['adjustment_type']='ExactCapacity'
    target = {}
    step._process_step_scaling_policy_configuration_adjustment_type(source, target)
    assert target['AdjustmentType'] == source['adjustment_type']

def test_process_step_scaling_policy_configuration_cooldown_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['cooldown']='a'
        target = {}
        step._process_step_scaling_policy_configuration_cooldown(source, target)

def test_process_step_scaling_policy_configuration_cooldown_valid():
    source = {}
    source['cooldown']= 60
    target = {}
    step._process_step_scaling_policy_configuration_cooldown(source, target)
    assert target['Cooldown'] == source['cooldown']

def test_process_step_scaling_policy_configuration_metric_aggregation_type_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['metric_aggregation_type']='a'
        target = {}
        step._process_step_scaling_policy_configuration_metric_aggregation_type(source, target)

def test_process_step_scaling_policy_configuration_metric_aggregation_type_valid():
    source = {}
    
    source['metric_aggregation_type']='Average'
    target = {}
    step._process_step_scaling_policy_configuration_metric_aggregation_type(source, target)
    assert target['MetricAggregationType'] == source['metric_aggregation_type']

    source['metric_aggregation_type']='Minimum'
    target = {}
    step._process_step_scaling_policy_configuration_metric_aggregation_type(source, target)
    assert target['MetricAggregationType'] == source['metric_aggregation_type']

    source['metric_aggregation_type']='Maximum'
    target = {}
    step._process_step_scaling_policy_configuration_metric_aggregation_type(source, target)
    assert target['MetricAggregationType'] == source['metric_aggregation_type']


def test_process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['metric_interval_lower_bound']='a'
        target = {}
        step._process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(source, target)

def test_process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound_valid():
    source = {}
    source['metric_interval_lower_bound']= 0
    target = {}
    step._process_step_scaling_policy_configuration_step_adjustments_metric_interval_lower_bound(source, target)
    assert target['MetricIntervalLowerBound'] == source['metric_interval_lower_bound']

def test_process_process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['metric_interval_upper_bound']='a'
        target = {}
        step._process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(source, target)

def test_process_process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound_valid():
    source = {}
    source['metric_interval_upper_bound']= 0
    target = {}
    step._process_step_scaling_policy_configuration_step_adjustments_metric_interval_upper_bound(source, target)
    assert target['MetricIntervalUpperBound'] == source['metric_interval_upper_bound']

def test_process_process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['scaling_adjustment']='a'
        target = {}
        step._process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(source, target)

def test_process_process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment_valid():
    source = {}
    source['scaling_adjustment']= 0
    target = {}
    step._process_step_scaling_policy_configuration_step_adjustments_scaling_adjustment(source, target)
    assert target['ScalingAdjustment'] == source['scaling_adjustment']

def test_process_cloudwatch_alarm_metric_name_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['metric_name']='a'
        target = {}
        step._process_cloudwatch_alarm_metric_name(source, target)

def test_process_cloudwatch_alarm_metric_name_empty():
    with pytest.raises(ValueError):
        source = {}
        target = {}
        step._process_cloudwatch_alarm_metric_name(source, target)

def test_process_cloudwatch_alarm_metric_name_valid():
    source = {}
    source['metric_name']='CPUUtilization'
    target = {}
    step._process_cloudwatch_alarm_metric_name(source, target)
    assert target['MetricName'] == source['metric_name']

    source['metric_name']='MemoryUtilization'
    target = {}
    step._process_cloudwatch_alarm_metric_name(source, target)
    assert target['MetricName'] == source['metric_name']

def test_process_cloudwatch_alarm_alarm_description_empty():
    source = {}
    target = {}
    target['MetricName'] = 'CPUUtilization'
    step._process_cloudwatch_alarm_alarm_description(source, target)
    assert target['AlarmDescription'] == f'Containers {target["MetricName"]} High'

def test_process_cloudwatch_alarm_alarm_description_not_empty():
    source = {}
    target = {}
    target['MetricName'] = 'CPUUtilization'
    source['alarm_description']='test'
    step._process_cloudwatch_alarm_alarm_description(source, target)
    assert target['AlarmDescription'] == source['alarm_description']

def test_process_cloudwatch_alarm_namespace():
    source = {}
    expected= {}
    source['namespace'] = 'test'
    step._process_cloudwatch_alarm_namespace(source, expected)
    assert expected['Namespace'] == source['namespace']

def test_process_cloudwatch_alarm_statistic_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['statistic']='a'
        target = {}
        step._process_cloudwatch_alarm_statistic(source, target)

def test_process_cloudwatch_alarm_statistic_valid():
    source = {}
    target = {}

    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == 'Average'
    
    source['statistic']='Average'
    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == source['statistic']

    source['statistic']='Minimum'
    target = {}
    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == source['statistic']

    source['statistic']='Maximum'
    target = {}
    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == source['statistic']

    source['statistic']='SampleCount'
    target = {}
    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == source['statistic']

    source['statistic']='Sum'
    target = {}
    step._process_cloudwatch_alarm_statistic(source, target)
    assert target['Statistic'] == source['statistic']

def test_process_cloudwatch_alarm_period_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['period']='a'
        target = {}
        step._process_cloudwatch_alarm_period(source, target)

def test_process_cloudwatch_alarm_period_valid():
    source = {}
    source['period']= 60
    target = {}
    step._process_cloudwatch_alarm_period(source, target)
    assert target['Period'] == source['period']

def test_process_cloudwatch_alarm_evaluation_periods_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['evaluation_periods']='a'
        target = {}
        step._process_cloudwatch_alarm_evaluation_periods(source, target)

def test_process_cloudwatch_alarm_evaluation_periods_valid():
    source = {}
    source['evaluation_periods']= 2
    target = {}
    step._process_cloudwatch_alarm_evaluation_periods(source, target)
    assert target['EvaluationPeriods'] == source['evaluation_periods']

def test_process_cloudwatch_alarm_evaluation_threshold_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['threshold']='a'
        target = {}
        step._process_cloudwatch_alarm_threshold(source, target)

def test_process_cloudwatch_alarm_evaluation_threshold_required():
    with pytest.raises(ValueError):
        source = {}
        target = {}
        step._process_cloudwatch_alarm_threshold(source, target)

def test_process_cloudwatch_alarm_evaluation_periods_valid():
    source = {}
    source['threshold']= 50
    target = {}
    step._process_cloudwatch_alarm_threshold(source, target)
    assert target['Threshold'] == source['threshold']

def test_process_cloudwatch_alarm_comparison_operator_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['comparison_operator']='a'
        target = {}
        step._process_cloudwatch_alarm_comparison_operator(source, target)

def test_process_cloudwatch_alarm_comparison_operator_required():
    with pytest.raises(ValueError):
        source = {}
        target = {}
        step._process_cloudwatch_alarm_comparison_operator(source, target)

def test_process_cloudwatch_alarm_comparison_operator_valid():
    source = {}
    target = {}
    
    source['comparison_operator']='GreaterThanOrEqualToThreshold'
    step._process_cloudwatch_alarm_comparison_operator(source, target)
    assert target['ComparisonOperator'] == source['comparison_operator']

    source['comparison_operator']='GreaterThanThreshold'
    step._process_cloudwatch_alarm_comparison_operator(source, target)
    assert target['ComparisonOperator'] == source['comparison_operator']

    source['comparison_operator']='LessThanOrEqualToThreshold'
    step._process_cloudwatch_alarm_comparison_operator(source, target)
    assert target['ComparisonOperator'] == source['comparison_operator']

    source['comparison_operator']='LessThanThreshold'
    step._process_cloudwatch_alarm_comparison_operator(source, target)
    assert target['ComparisonOperator'] == source['comparison_operator']

def test_process_scheduling_strategy_invalid():
    with pytest.raises(ValueError):
        source = {}
        source['scheduling_strategy']='a'
        target = {}
        step._process_scheduling_strategy(source, target)

def test_process_scheduling_strategy_valid():
    source = {}
    target = {}
    
    source['scheduling_strategy']='DAEMON'
    step._process_scheduling_strategy(source, target)
    assert target['SchedulingStrategy'] == source['scheduling_strategy']

    source['scheduling_strategy']='REPLICA'
    step._process_scheduling_strategy(source, target)
    assert target['SchedulingStrategy'] == source['scheduling_strategy']

def test_process_application_autoscaling_scalable_target_min_capacity_valid():
    source = {}
    target = {}
    
    # default value
    step.infos.scale_infos = ScaleInfos()
    step.infos.scale_infos.desired = 2
    step._process_application_autoscaling_scalable_target_min_capacity(source, target)
    assert target['MinCapacity'] == step.infos.scale_infos.desired 
    
    # set valude
    source['min_capacity'] = 1
    step._process_application_autoscaling_scalable_target_min_capacity(source, target)
    assert target['MinCapacity'] == source['min_capacity']  

def test_process_application_autoscaling_scalable_target_max_capacity_invalid():
    source = {}
    source['max_capacity'] = 'a'
    target = {}
    with pytest.raises(ValueError):
        step._process_application_autoscaling_scalable_target_max_capacity(source, target)

def test_process_application_autoscaling_scalable_target_max_capacity_valid():
    source = {}
    target = {}
    
    # default value
    step.infos.scale_infos = ScaleInfos()
    step.infos.scale_infos.desired = 2
    step._process_application_autoscaling_scalable_target_max_capacity(source, target)
    assert target['MaxCapacity'] == step.infos.scale_infos.desired 
    
    # set valude
    source['max_capacity'] = 1
    step._process_application_autoscaling_scalable_target_max_capacity(source, target)
    assert target['MaxCapacity'] == source['max_capacity']  

def test_process_application_autoscaling_scalable_target_role_arn_valid():
    source = {}
    target = {}
    source['role_arn'] = 'a'
    step._process_application_autoscaling_scalable_target_role_arn(source, target)
    assert target['RoleARN'] == source['role_arn']

def test_process_application_autoscaling_scalable_target_role_arn_required():
    source = {}
    target = {}
    with pytest.raises(ValueError):
        step._process_application_autoscaling_scalable_target_role_arn(source, target)

def test_process_application_auto_scaling_scaling_policy_policy_type_invalid():
    source = {}
    target = {}
    with pytest.raises(ValueError):
        source['policy_type']='a'
        step._process_application_auto_scaling_scaling_policy_policy_type(source, target)
   
def test_process_application_auto_scaling_scaling_policy_policy_type_valid():
    source = {}
    target = {}
    
    source['policy_type']='SimpleScaling'
    step._process_application_auto_scaling_scaling_policy_policy_type(source, target)
    assert target['PolicyType'] == source['policy_type']

    source['policy_type']='StepScaling'
    step._process_application_auto_scaling_scaling_policy_policy_type(source, target)
    assert target['PolicyType'] == source['policy_type']

    source['policy_type']='TargetTrackingScaling'
    step._process_application_auto_scaling_scaling_policy_policy_type(source, target)
    assert target['PolicyType'] == source['policy_type']

def test_process_placement_stategies_strategy_field_required():
    source = {}
    target = {}
    with pytest.raises(ValueError):
        step._process_placement_stategies_strategy_field(source, target)

def test_process_placement_stategies_strategy_field_valid():
    source = {}
    source['field'] ='test'
    target = {}
    step._process_placement_stategies_strategy_field(source, target)
    assert target['Field'] == source['field']

def test_process_placement_stategies_strategy_type_required():
    source = {}
    target = {}
    with pytest.raises(ValueError):
        step._process_placement_stategies_strategy_type(source, target)

def test_process_placement_stategies_strategy_field_invalid():
    source = {}
    source['type']='test'
    target = {}
    with pytest.raises(ValueError):
        step._process_placement_stategies_strategy_type(source, target)

def test_process_placement_stategies_strategy_field_valid():
    source = {}
    source['type']='binpack'
    target = {}
    step._process_placement_stategies_strategy_type(source, target)
    assert target['Type'] == source['type']

    source['type']='random'
    target = {}
    step._process_placement_stategies_strategy_type(source, target)
    assert target['Type'] == source['type']

    source['type']='spread'
    target = {}
    step._process_placement_stategies_strategy_type(source, target)
    assert target['Type'] == source['type']
    
def test_process_placement_constraints_contraint_type_required():
    source = {}
    target = {}
    with pytest.raises(ValueError):
        step._process_placement_constraints_contraint_type(source, target)

def test_process_placement_stategies_strategy_type_invalid():
    source = {}
    source['type']='test'
    target = {}
    with pytest.raises(ValueError):
        step._process_placement_constraints_contraint_type(source, target)

def test_process_placement_stategies_strategy_type_valid():
    source = {}
    source['type']='distinctInstance'
    target = {}
    step._process_placement_constraints_contraint_type(source, target)
    assert target['Type'] == source['type']

    source['type']='memberOf'
    target = {}
    step._process_placement_constraints_contraint_type(source, target)
    assert target['Type'] == source['type']
