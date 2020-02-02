#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTargetGroupsStep import PrepareDeploymentTargetGroupsStep
from ecs_crd.sendNotificationBySnsStep import SendNotificationBySnsStep

class PrepareDeploymentTaskDefinitionStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, f'Prepare {infos.action} ( Task definition )', logger)

    def _process_cpu(self, item, cfn):
        if 'cpu' in item:
            cfn['Cpu'] = int(item['cpu'])
            self._log_information(key='Cpu', value=cfn["Cpu"], ljust=10, indent=1)

    def _process_memory(self, item, cfn):
        if 'memory' in item:
            cfn['Memory'] = int(item['memory'])
            self._log_information(key='Memory', value=cfn["Memory"], ljust=10, indent=1)

    def _process_network_mode(self, item, cfn):
        if 'network_mode' in item:
            cfn['NetworkMode'] = item['network_mode']
            self._log_information(key='NetworkMode', value=cfn["NetworkMode"], ljust=10, indent=1)

    def _process_pid_mode(self, item, cfn):
        if 'pid_mode' in item:
            cfn['PidMode'] = item['pid_mode']
            self._log_information(key='PidMode', value=cfn["PidMode"], ljust=10, indent=1)

    def _process_ipc_mode(self, item, cfn):
        if 'ipc_mode' in item:
            cfn['IpcMode'] = item['ipc_cmode']
            self._log_information(key='IpcMode', value=cfn["IpcMode"], ljust=10, indent=1)

    def _process_requires_compatibilities(self, item, cfn):
        if 'requires_compatibilities' in item:
            self._log_information(key='Requires Compatibilities', value='', ljust=10, indent=1)
            cfn['RequiresCompatibilities'] =[]
            for e in item['requires_compatibilities']:
                cfn['RequiresCompatibilities'].append(e)
                self._log_information(key='- '+e, value=None, ljust=10, indent=1)

    def _process_volumes(self, item, cfn):
        if 'volumes' in item:
            cfn['Volumes'] = []
            self._log_information(key='Volumes', value=None, ljust=10, indent=1)
            for e in item['volumes']:
                volume = {}
                volume['Name'] = self._bind_data(item['name'])
                self._log_information(key='- Name', value=volume['Name'], ljust=10, indent=2)
                if 'docker_volume_configuration' in e:
                    volume['DockerVolumeConfiguration'] = {}
                    self._process_docker_volume_configuration(e['docker_volume_configuration'], volume['DockerVolumeConfiguration'])
                if 'host' in e:
                    volume['Host'] = {}
                    self._process_host(e['host'],volume['Host'])
                cfn['Volumes'].append(volume)

    def _process_host(self, item, cfn):
        self._log_information(key='Host', value=None, ljust=10, indent=4)
        if 'source_path' in item:
            cfn['SourcePath'] = self._bind_data(item['source_path'])
            self._log_information(key='SourcePath', value=cfn['SourcePath'], ljust=10, indent=5)

    def _process_docker_volume_configuration(self, item, cfn):
        self._log_information(key='DockerVolumeConfiguration', value=None, ljust=10, indent=4)
        if 'autoprovision' in item:
            cfn['Autoprovision'] = str(item['autoprovision'])
            self._log_information(key='Autoprovision', value=cfn['Autoprovision'], ljust=10, indent=5)
        if 'driver' in item:
            cfn['Driver'] = str(item['driver'])
            self._log_information(key='Driver', value=cfn['Driver'], ljust=10, indent=5)
        if 'driver_opts' in item:
            cfn['DriverOpts'] = []
            self._log_information(key='DriverOpts', value=None, ljust=10, indent=5)
            # TODO fix
            for e in item['driver_opts']:
                elmt = {}
                key = None
                value = None
                for a in e.keys():
                    key = a
                for a in elmt.values():
                    value = str(a)
                elmt[key] = value
                cfn['DriverOpts'].append(elmt)
                self._log_information(key='- '+key, value=value, ljust=10, indent=6)
        if 'labels' in item:
            self._log_information(key='Labels', value=None, ljust=10, indent=5)
            cfn['Labels'] = []
            for e in item['labels']:
                elmt = {}
                key = None
                value = None
                for a in e.keys():
                    key = a
                for a in elmt.values():
                    value = str(a)
                elmt[key] = self._bind_data(value)
                cfn['Labels'].append(elmt)
                self._log_information(key='- '+key, value=value, ljust=10, indent=6)
        if 'scope' in item:
            cfn['Scope'] = item['scope']
            self._log_information(key='Scope', value=cfn['Scope'], ljust=10, indent=5)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            cfn = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']
            item = self.configuration['service']
            self._process_cpu(item, cfn)
            self._process_memory(item, cfn)
            self._process_network_mode(item, cfn)
            self._process_ipc_mode(item, cfn)
            self._process_pid_mode(item, cfn)
            self._process_requires_compatibilities(item, cfn)
            self._process_volumes(item, cfn)
            self.infos.save()
            return PrepareDeploymentTargetGroupsStep(self.infos, self.logger)         

        except Exception as e:
            self.infos.exit_code = 6
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
            return SendNotificationBySnsStep(self.infos, self.logger)

