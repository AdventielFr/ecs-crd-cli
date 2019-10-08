#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import StrategyInfos
from ecs_crd.prepareDeploymentInitStackStep import PrepareDeploymentInitStackStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentStrategyStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Canary Strategy )', logger)
        self.min_wait = 40
        self.default_weight = 50
        self.default_wait = 60

    def _process_strategy(self):
        """update strategies informations for the service"""
        source = self.configuration['canary']
        if 'strategy' in source:
            for item in source['strategy']:
                wait = self.default_wait
                if 'wait' in item:
                    wait = int(item['wait'])
                if wait < self.min_wait:
                    wait = self.min_wait
                weight = self.default_weight
                if 'weight' in item:
                    weight = int(item['weight'])
                self.infos.strategy_infos.append(StrategyInfos(weight=weight, wait=wait))

        # no previous stack ( go to 100% )
        if not self.infos.blue_infos.stack_id:
            self.infos.strategy_infos.clear()

        self.infos.strategy_infos.append(StrategyInfos(weight=100, wait=self.default_wait))
        self.infos.strategy_infos = sorted(self.infos.strategy_infos, key=lambda strategy: strategy.weight)        

        for a in self.infos.strategy_infos:
            self._log_information(key='- Weight', value=a.weight, indent=1)
            self._log_information(key='  Wait', value=f'{a.wait}s', indent=1)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_strategy()
            return PrepareDeploymentInitStackStep(self.infos,self.logger)
        except Exception as e:
            self.infos.exit_code = 10
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)