
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTargetGroupsStep import PrepareDeploymentTargetGroupsStep

class PrepareDeploymentTaskDefinitionStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Task definition )', logger)

    def _process_cpu(self, item, cfn):
        if 'cpu' in item:
            cfn['Cpu'] = int(item['cpu'])
            self.logger.info(f' Cpu : {cfn["Cpu"]}')

    def _process_memory(self, item, cfn):
        if 'memory' in item:
            cfn['Memory'] = int(item['memory'])
            self.logger.info(f' Memory :  {cfn["Memory"]}')

    def _process_network_mode(self, item, cfn):
        if 'network_mode' in item:
            cfn['NetworkMode'] = item['network_mode']
            self.logger.info(f' NetworkMode:  {cfn["NetworkMode"]}')

    def _process_requires_compatibilities(self, item, cfn):
        if 'requires_compatibilities' in item:
            cfn['RequiresCompatibilities'] = item['requires_compatibilities']
            self.logger.info(f' NetworkMode :  {cfn["RequiresCompatibilities"]}')

    def _process_volume(self, item, cfn):
        if 'volumes' in item:
            self.logger.info(f' Volumnes :')
            cfn['Volumes'] = []
            for e in item['volumes']:
                volume = {}
                volume['Host'] = {}
                volume['Host']['SourcePath'] = e['host']
                volume['Name'] = e['name']
                cfn['Volumes'].append(volume)
                self.logger.info('     SourcePath: {}'.format( volume['Host']['SourcePath'] ))
                self.logger.info('     Name: {}'.format(volume['Name']))

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self.logger.info('')
            self.logger.info('Task definition infos :')
            self.logger.info(''.ljust(50, '-'))
            cfn = self.infos.green_infos.stack['Resources']['TaskDefinition']
            item = self.configuration['service']
            self._process_cpu(item, cfn)
            self._process_memory(item, cfn)
            self._process_network_mode(item, cfn)
            self._process_requires_compatibilities(item, cfn)
            self._process_volume(item, cfn)
            self.infos.save()
            return PrepareDeploymentTargetGroupsStep(self.infos, self.logger)         

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

   