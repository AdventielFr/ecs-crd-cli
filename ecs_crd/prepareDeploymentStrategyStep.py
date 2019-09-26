#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import StrategyInfos
from ecs_crd.createInitStackStep import CreateInitStackStep


class PrepareDeploymentStrategyStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Canary Strategy )', logger)
        self.min_wait = 40
        self.default_weight = 50
        self.default_wait = 60

    def _process_strategy(self):
        """update strategies informations for the service"""
        if 'strategy' in self.configuration['canary']:
            for item in self.configuration['canary']['strategy']:
                wait = self.default_wait
                if 'wait' in item:
                    wait = int(item['wait'])
                if wait < self.min_wait:
                    wait = self.min_wait
                weight = self.default_weight
                if 'weight' in item:
                    weight = int(item['weight'])
                self.infos.strategy_infos.append(StrategyInfos(weight, wait))
        else:
            self.infos.strategy_infos.append(StrategyInfos(self.default_weight, self.default_wait))

        # no previous stack ( go to 100% )
        if not self.infos.blue_infos.stack_id:
            self.infos.strategy_infos.clear()

        self.infos.strategy_infos.append(StrategyInfos(100, self.default_wait))
        self.infos.strategy_infos = sorted(self.infos.strategy_infos, key=lambda strategy: strategy.weight)        

        for a in self.infos.strategy_infos:
            self._log_information(key='- Weight', value=a.weight, indent=1)
            self._log_information(key='  Wait', value='{}s'.format(a.wait), indent=1)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_strategy()
            return CreateInitStackStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None
