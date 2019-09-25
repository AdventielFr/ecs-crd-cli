#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTaskDefinitionStep import PrepareDeploymentTaskDefinitionStep


class PrepareDeploymentServiceDefinitionStep(CanaryReleaseDeployStep):

    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Service definition )', logger)

    def _process_scheduling_strategy(self):
        """update the sceduling stratégy informations for the service"""
        self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'REPLICA'
        if 'scheduling_strategy' in self.configuration['service']:
            if self.configuration['service']['scheduling_strategy'].upper() == 'DAEMON':
                self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'DAEMON'
        self._log_information(key='Scheduling Strategy', value=self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'], ljust=10, indent=1)

    def _process_platform_version(self):
        """update the plaform version informations for the service"""
        if 'platform_version' in self.configuration['service']:
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion'] = self.configuration['service']['platform_version']
            self._log_information(key='Platform Version', value=self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion'], ljust=10, indent=1)

    def _process_placement_constraints(self):
        """update the placement constraintes informations for the service"""
        if 'placement_constraints' in self.configuration['service']:
            self._log_information(key='Placement Contraints', value='', ljust=10, indent=1)
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'] = []
            for item in self.configuration['service']['placement_constraints']:
                constraint = {}
                if 'expression' in item:
                    constraint['Expression'] = item['expression']
                constraint['Type'] = item['type']
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'].append(constraint)
                self._log_information(key='- Expression', value=constraint['Expression'], ljust=10, indent=2)
                self._log_information(key='  Type', value=constraint['Type'], ljust=10, indent=2)

    def _process_placement_stategies(self):
        """update the placement strategies informations for the service"""
        if 'placement_stategies' in self.configuration['service']:
            self._log_information(key='Placement Strategies',value='', ljust=10, indent=1)
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'] = []
            for item in self.configuration['service']['placement_stategies']:
                strategy = {}
                strategy['Field'] = item['field']
                strategy['Type'] = item['type']
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'].append(strategy)
                self._log_information(key='- Field',value=strategy['Field'], ljust=10, indent=2)
                self._log_information(key='  Type',value=strategy['Type'], ljust=10, indent=2)

    def _process_load_balancer(self):
        cfn = self.infos.green_infos.stack['Resources']['Service']['Properties']['LoadBalancers']
        for item in self.configuration['service']['containers']:
            if 'port_mappings' in item:
                for e in item['port_mappings']:
                    definition = {}
                    container_name = 'default'
                    if 'name' in item:
                        container_name = item['name']
                    definition['ContainerName'] =  container_name
                    definition['ContainerPort'] = int(e['container_port'])
                    definition['TargetGroupArn'] = {}
                    w = definition['ContainerName'] + '_' + str(e['container_port'])
                    definition['TargetGroupArn']['Ref'] = "TargetGroup{}".format(''.join(id.capitalize() for id in w.split('_')))
                    cfn.append(definition)

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:
            self._process_scheduling_strategy()
            self._process_platform_version()
            self._process_placement_constraints()
            self._process_placement_stategies()
            self._process_load_balancer()
            self.infos.save()
            return PrepareDeploymentTaskDefinitionStep(self.infos, self.logger)
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None
