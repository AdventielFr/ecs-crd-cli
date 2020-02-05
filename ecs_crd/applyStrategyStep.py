#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.rollbackChangeRoute53WeightsStep import RollbackChangeRoute53WeightsStep
from ecs_crd.updateCanaryReleaseInfoStep import UpdateCanaryReleaseInfoStep

class ChangeRoute53WeightsStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
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
        """update balancing ratio beetween blue's and green's DNS"""
        # by default 100 % for green / 0% for blue
        green_weight, blue_weight = (100, 0)
        # if exist canary strategy , set weights
        if (strategy):
            green_weight = strategy.weight
            blue_weight = 100 - green_weight

        self.logger.info('')
        self._log_information(key='Dns weight blue', value=f"{blue_weight}%")
        self._log_information(key='Dns weight green', value=f"{green_weight}%")
        self.logger.info('')

        client = boto3.client('route53')
        for item in self.infos.fqdn:
            self._change_weights_by_fqdn(item, client, blue_weight, green_weight)

        if (green_weight == 100):
            self.infos.strategy_infos.clear()
        self.logger.info('')
        self._wait(strategy.wait, "Changing DNS's Weights")

    def _change_weights_by_fqdn(self, fqdn, client, blue_weight, green_weight):
        self._log_information(key='Fqdn', value=fqdn.name)
        client.change_resource_record_sets(
            HostedZoneId = fqdn.hosted_zone_id,
            ChangeBatch={
                'Comment': 'Alter Route53 records sets for canary blue-green deployment',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': f"{fqdn.name}.",
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.blue_infos.canary_release,
                            'Weight': blue_weight,
                            'TTL': 60,
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
                            'Name': f"{fqdn.name}.",
                            'Type': 'CNAME',
                            'SetIdentifier': self.infos.green_infos.canary_release,
                            'Weight': green_weight,
                            'TTL': 60,
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
       

    def _consume_strategy(self):
        """consume the first strategy of the canary release's definition"""
        result = None
        if self.infos.strategy_infos:
            result, tmp = (self.infos.strategy_infos[0],
                           self.infos.strategy_infos[1:])
            self.infos.strategy_infos = tmp
        return result


class CheckGreenHealthStep(CanaryReleaseDeployStep):
    """ Check health status of Green's """

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        self._nb_max_initial_test = 4
        self._nb_initial_test = 1
        super().__init__(infos, 'Check Health Green LoadBalancer', logger)

    def _find_health_checks(self):
        """return list of state of health check load balancer"""
        result = []
        client = boto3.client('elbv2', region_name=self.infos.region)
        targetGroupArns = self._find_target_group_arns()
        for e in targetGroupArns:
            response = client.describe_target_health(TargetGroupArn=e['OutputValue'])
            state = "UNKNOWN"
            if response['TargetHealthDescriptions']:
                state = response['TargetHealthDescriptions'][0]['TargetHealth']['State'].upper()
            self.logger.info('')
            self._log_information(key='Target Group', value=e['OutputKey'][:-3])
            self._log_information(key='Arn', value=e['OutputValue'])
            self._log_information(key='State', value=state)
            result.append(state)
        return result

    def _is_all_full_states(self, health_checks, states):
        if not states:
            return False
        return len(list(filter(lambda x: x in states, health_checks))) == len(health_checks)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            while True:
                health_checks = self._find_health_checks()
                is_full_healthy = self._is_all_full_states(health_checks, ['HEALTHY'])
                if is_full_healthy:
                    break
                is_healthy_and_initial = self._is_all_full_states(health_checks, ['HEALTHY', 'INITIAL'])
                if is_healthy_and_initial:
                    if self._nb_initial_test < self._nb_max_initial_test:
                        self._wait(15, f'Waiting for service to start (attempts {self._nb_initial_test}/{self._nb_max_initial_test})')
                        self._nb_initial_test += 1
                        continue
                raise ValueError(f'Invalid state for Green TargetGroup')
            # all health check is ok
            if self.infos.strategy_infos:
                return ChangeRoute53WeightsStep(self.infos, self.logger)
            else:
                return UpdateCanaryReleaseInfoStep(self.infos, self.logger)

        except Exception as e:
            self.logger.error('CheckGreenHealthStep', exc_info=True)
            self.infos.exit_exception = e
            self.infos.exit_code = 14
            return RollbackChangeRoute53WeightsStep(self.infos, self.logger)

    def _find_target_group_arns(self):
        client = boto3.client('cloudformation', region_name=self.infos.region)
        response = client.describe_stacks(StackName= self.infos.green_infos.stack_name)
        return  filter(lambda x: x['OutputKey'].startswith('TargetGroup'),response['Stacks'][0]['Outputs'])
        