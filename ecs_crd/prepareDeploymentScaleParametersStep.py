
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.canaryReleaseInfos import ScaleInfos
from ecs_crd.prepareDeploymentLoadBalancerParametersStep import PrepareDeploymentLoadBalancerParametersStep

class PrepareDeploymentScaleParametersStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Scale parameters )', logger)
        self.min_wait = 40

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            desired = 2
            wait = self.min_wait 
            if 'scale' in self.configuration['canary']:
                scale = self.configuration['canary']['scale']
                if 'desired' in scale:
                    desired = int(scale['desired'])
                if 'wait' in scale:
                    wait = int(scale['wait'])
            if wait < self.min_wait:
                wait = self.min_wait
            self.infos.scale_infos = ScaleInfos(desired, wait)
            
            self._log_information(key='Desired  Instances', value=desired , ljust=18)
            self._log_information(key='Wait', value=f'{wait}s' , ljust=18)
            self.infos.save()
            
            return PrepareDeploymentLoadBalancerParametersStep(self.infos, self.logger)

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

   