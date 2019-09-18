
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTargetGroupsStep import PrepareDeploymentTargetGroupsStep

class PrepareDeploymentTaskDefinitionStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Task definition )', logger)

    def _process_cpu(self, item, cfn):
        if 'cpu' in item:
            cfn['Cpu'] = int(item['cpu'])
            self._log_information(key='Cpu',value=cfn["Cpu"],ljust=10, indent=1)

    def _process_memory(self, item, cfn):
        if 'memory' in item:
            cfn['Memory'] = int(item['memory'])
            self._log_information(key='Memory',value=cfn["Memory"],ljust=10, indent=1)

    def _process_network_mode(self, item, cfn):
        if 'network_mode' in item:
            cfn['NetworkMode'] = item['network_mode']
            self._log_information(key='NetworkMode',value=cfn["NetworkMode"],ljust=10, indent=1)

    def _process_pid_mode(self, item, cfn):
        if 'pid_mode' in item:
            cfn['PidMode'] = item['pid_mode']
            self._log_information(key='PidMode',value=cfn["PidMode"],ljust=10, indent=1)

    def _process_ipc_mode(self, item, cfn):
        if 'ipc_mode' in item:
            cfn['IpcMode'] = item['ipc_cmode']
            self._log_information(key='IpcMode',value=cfn["IpcMode"],ljust=10, indent=1)

    def _process_requires_compatibilities(self, item, cfn):
        if 'requires_compatibilities' in item:
            self._log_information(key='Requires Compatibilities',value='',ljust=10, indent=1)
            cfn['RequiresCompatibilities'] =[]
            for e in item['requires_compatibilities']:
                cfn['RequiresCompatibilities'].append(e)
                self._log_information(key='- '+e, value=None,ljust=10, indent=1)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            cfn = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']
            item = self.configuration['service']
            self._process_cpu(item, cfn)
            self._process_memory(item, cfn)
            self._process_network_mode(item, cfn)
            self._process_ipc_mode(item, cfn)
            self._process_pid_mode(item,cfn)
            self._process_requires_compatibilities(item, cfn)
            self.infos.save()
            return PrepareDeploymentTargetGroupsStep(self.infos, self.logger)         

        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

   