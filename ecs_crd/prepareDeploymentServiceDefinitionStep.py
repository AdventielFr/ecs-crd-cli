
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentTaskDefinitionStep import PrepareDeploymentTaskDefinitionStep

class PrepareDeploymentServiceDefinitionStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos,'Prepare deployment ( Service definition )', logger)

    def _process_scheduling_strategy(self):
        """update the sceduling stratégy informations for the service"""
        if 'scheduling_strategy' in self.configuration['service']:
            if self.configuration['service']['scheduling_strategy'].upper() == 'DAEMON':
                self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'DAEMON'
            else:
                self.infos.green_infos.stack['Resources']['Service']['Properties']['SchedulingStrategy'] = 'REPLICA'
            self.logger.info( ' Scheduling Strategy: {}'.format(self.infos.green_infos.stack['Resources']['Service']['SchedulingStrategy']))

    def _process_platform_version(self):
        """update the plaform version informations for the service"""
        if 'platform_version' in self.configuration['service']:
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion'] = self.configuration['service']['platform_version']
            self.logger.info( ' Platform Version: {}'.format(self.infos.green_infos.stack['Resources']['Service']['Properties']['PlatformVersion']))

    def _process_placement_constraints(self):
        """update the placement constraintes informations for the service"""
        if 'placement_constraints' in self.configuration['service']:
            self.logger.info(' Placement Constraints infos:')
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'] = []
            for item in self.configuration['service']['placement_constraints']:
                constraint = {}
                constraint['Expression'] = item['expression']
                constraint['Type'] = item['type']
                self.logger.info('  Expression: {}'.format(item['expression']))
                self.logger.info('  Type: {}'.format(item['type']))
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementConstraints'].append(constraint)

    def _process_placement_stategies(self):
        """update the placement strategies informations for the service"""
        if 'placement_stategies' in self.configuration['service']:
            self.logger.info(' Placement Strategies infos:')
            self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'] = []
            for item in self.configuration['service']['placement_stategies']:
                strategy = {}
                strategy['Field'] = item['field']
                strategy['Type'] = item['type']
                self.logger.info('  Field: {}'.format(item['field']))
                self.logger.info('  Type: {}'.format(item['type']))
                self.infos.green_infos.stack['Resources']['Service']['Properties']['PlacementStrategies'].append(strategy)

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
            self.logger.info('')
            self.logger.info('Service infos :')
            self.logger.info(''.ljust(50, '-'))
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

   