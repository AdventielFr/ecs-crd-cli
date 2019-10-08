#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.prepareDeploymentContainerDefinitionsStep import PrepareDeploymentContainerDefinitionsStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentScaleParametersStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Scale parameters )', logger)
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
            self._log_information(key='Desired  Instances', value=self.infos.scale_infos.desired, ljust=18)
            self._log_information(key='Wait', value=f'{wait}s', ljust=18)
            self.infos.save()
            return PrepareDeploymentContainerDefinitionsStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 3
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)