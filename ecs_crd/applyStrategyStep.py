import boto3
import time
import json
import traceback

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.rollbackChangeRoute53WeightsStep import RollbackChangeRoute53WeightsStep
from ecs_crd.updateCanaryReleaseInfoStep import UpdateCanaryReleaseInfoStep
from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder

class ChangeRoute53WeightsStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        self._nb_max_initial_test = 3
        self._nb_initial_test = 0
        super().__init__(infos, 'Change Route 53 Weights', logger)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            strategy = self._consume_strategy()
            self._change_weights(strategy)
            return CheckGreenHealthStep(self.infos, self.logger)
        except Exception as e:
            self.logger.error('ChangeRoute53WeightsStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 5
            return RollbackChangeRoute53WeightsStep(self.infos, self.logger)


    def _change_weights(self, strategy):
        """change weight beetween blue DNS and green DNS"""
        client = boto3.client('route53')
        # by default 100 % for green / 0% for blue
        green_weight = 100
        blue_weight = 0
        # if exist canary strategy , set weights
        if strategy != None:
            green_weight = strategy.weight
            blue_weight = 100 - green_weight

        self.logger.info('')
        self.logger.info(' Blue {}% <-=-> {}% Green'.format(str(blue_weight).rjust(3),str(green_weight).rjust(3)))
        self.logger.info('')

        client.change_resource_record_sets(
            HostedZoneId = self.infos.hosted_zone_id,
            ChangeBatch={
                'Comment': 'Alter Route53 records sets for canary blue-green deployment',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': self.infos.fqdn + '.',
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.blue_infos.canary_release,
                            'Weight': blue_weight,
                            'TTL' : 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.blue_infos.alb_dns
                                },
                            ]
                        }, 
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': self.infos.fqdn + '.',
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.green_infos.canary_release,
                            'Weight': green_weight,
                            'TTL' : 60,
                            'ResourceRecords': [
                                {
                                    'Value': self.infos.green_infos.alb_dns
                                },
                            ]
                        },
                    }
                ]
            }
        )
        if (green_weight == 100):
            self.infos.strategy_infos.clear()
        self.wait(strategy.wait, 'Change DNS Weights in progress')

    def _consume_strategy(self):
        """consume the first strategy of the canary release definition"""
        result = None
        if len(self.infos.strategy_infos) > 0:
            tmp = []
            for i in range(0, len(self.infos.strategy_infos)):
                if i == 0:
                    result = self.infos.strategy_infos[i]
                else:
                    tmp.append(self.infos.strategy_infos[i])
            self.infos.strategy_infos = tmp
        return result

class CheckGreenHealthStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        self._nb_max_initial_test = 3
        self._nb_initial_test = 1
        super().__init__(infos, 'Check Health Green LoadBalancer', logger)

    def _find_health_checks(self):
        """return list of state of health check load balancer"""
        result =[]
        client = boto3.client('elbv2', region_name=self.infos.region)
        targetGroupArns = self._find_target_group_arns(client)
        for e in targetGroupArns:
            response = client.describe_target_health(TargetGroupArn=e)
            state = "UNKNOWN"
            if len(response['TargetHealthDescriptions']) > 0:
                state = response['TargetHealthDescriptions'][0]['TargetHealth']['State'].upper()
            self.logger.info(f'Target Group')
            self.logger.info(f'  Arn    : {e}')
            self.logger.info(f'  State  : {state}')
            result.append(state)
        return result

    def _is_all_full_state(self, health_checks, states):
        if len(states) == 0:
            return False
        count = sum(1 for e in health_checks if e in states)
        return len(health_checks) == count   

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            while True:
                health_checks = self._find_health_checks()
                is_full_healthy = self._is_all_full_state(health_checks, ['HEALTHY'])
                if is_full_healthy:
                    break
                is_healthy_and_initial = self._is_all_full_state(health_checks,['HEALTHY','INITIAL'])
                if is_healthy_and_initial:
                    if self._nb_initial_test < self._nb_max_initial_test:
                        self._nb_initial_test = self._nb_initial_test + 1
                        self.wait(20, 'Change DNS Weights in progress')
                        continue
                raise ValueError(f'Invalid state for Green TargetGroup')
            # all health check is ok
            if len(self.infos.strategy_infos) > 0:
                return ChangeRoute53WeightsStep(self.infos, self.logger)
            else:
                return UpdateCanaryReleaseInfoStep(self.infos, self.logger)
                
        except Exception as e:
            self.logger.error('CheckGreenHealthStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 6
            return RollbackChangeRoute53WeightsStep(self.infos, self.logger)
    
    def _find_target_group_arns(self, client):
        """find all target group arn of the canary release"""
        target_groups = []
        result = []
        # find names of target groups
        for e in self.infos.green_infos.stack['Resources'].keys():
            v = self.infos.green_infos.stack['Resources'][e]
            if v['Type'].endswith('TargetGroup'):
                 if str(v['Properties']['HealthCheckEnabled']).lower() == 'true':
                    target_groups.append(v['Properties']['Name'])
        
        # find arns of target groups
        if len(self.infos.listener_rules_infos) == 0 :
            response = client.describe_listeners(LoadBalancerArn=self.infos.green_infos.alb_arn)
            for item in response['Listeners']:
                defaut_action = item['DefaultActions'][0]
                if defaut_action['Type'] == 'forward':
                    arns = []
                    arns.append(defaut_action['TargetGroupArn'])
                    response = client.describe_target_groups(TargetGroupArns=arns)
                    if 'TargetGroups' in response:
                        target_group = response['TargetGroups'][0]
                        if target_group['TargetGroupName'] in target_groups:
                            result.append(target_group['TargetGroupArn'])
        else:
            for item in self.infos.listener_rules_infos:
                response = client.describe_rules(ListenerArn = item.listener_arn)
                for rule in response['Rules']:
                    if str(rule['Priority']) == str(item.configuration['rule']['priority']):
                        for action in rule['Actions']:
                            if action['Type'] == 'forward':
                                result.append(action['TargetGroupArn'])

        return result


