#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3

from ecs_crd.finishDeploymentStep import FinishDeploymentStep
from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep

class SendNotificationBySnsStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initializes a new instance of the class"""
        super().__init__(infos, 'Send Notification', logger, with_end_log=True)

    def _find_sns_topic_notifcation(self):
        if 'sns_topic_notifications' in self.configuration['canary']:
            result = self.configuration['canary']['sns_topic_notifications']
            if self.infos.exit_code == 0 and 'on_success' in  result:
                return self._bind_data(result['on_success'])
            if self.infos.exit_code != 0 and 'on_fail' in  result:
                return self._bind_data(result['on_fail'])
            return None

    def _on_execute(self):
        if self.infos.action != 'validate':
            sns_topic_notification = self._find_sns_topic_notifcation()
            if sns_topic_notification:
                message = f'ECS canary {self.infos.action} of the "{self.infos.service_name}" service was successful.'
                if self.infos.exit_code != 0:
                    message = f'ECS canary {self.infos.action} of the "{self.infos.service_name}" service was failed.'
                message +=f'\nAccount        : {self.infos.account_id}'
                message +=f'\nRegion         : {self.infos.region}'
                message +=f'\nEnvironment    : {self.infos.environment}'
                message +=f'\nCluster        : {self.infos.cluster_name}'
                message +=f'\nProject        : {self.infos.project}'
                message +=f'\nService        : {self.infos.service_name}'
                message +=f'\nVersion        : {self.infos.service_version}'
                fqdn = ''
                for item in self.infos.fqdn:
                    fqdn += item.name + ','
                message +=f'\nFqdn           : {fqdn}'
                message +=f'\nExit Code      : {self.infos.exit_code}'
                message +=f'\nMessage        : {self.infos.exit_exception}'
                subject = '[SUCCESS]' if self.infos.exit_code == 0 else '[FAIL]'
                subject += f' {self.infos.action} - {self.infos.service_name}' 
                client = boto3.client('sns', region_name=self.infos.region)
                self._log_information(key='Sending Notification ... ', value=None)
                try:
                    client.publish(
                        TopicArn = sns_topic_notification,
                        Message = message,
                        Subject = subject
                    )
                    self._log_information(key='Notification sended with success.', value=None)
                except Exception as e:
                    if self.infos.exit_code == 0:
                        self.infos.exit_code = 100
                        self.infos.exit_exception = e
                    self.logger.error(self.title, exc_info=True)
            else:
                self._log_information(key='No notification to send', value=None)
        return FinishDeploymentStep(self.infos, self.logger)
