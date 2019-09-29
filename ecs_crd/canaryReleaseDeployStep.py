#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import logging
import yaml
import time
import datetime
import re

class CanaryReleaseDeployStep(ABC):

    def __init__(self, infos, title, logger, with_end_log=True, with_start_log=True):
        self.infos = infos
        self.title = title
        self.logger = logger
        self.with_start_log = with_start_log
        self.with_end_log = with_end_log
        self.previous_exit_code = self.infos.exit_code
        self.configuration = self._load_configuration()

    def execute(self):
        if self.with_start_log:
            self._log_start()
        result = self._on_execute()
        if self.with_end_log:
            self._log_end()
        return result

    def _log_start(self):
        self.logger.info(''.ljust(50, '-'))
        self.logger.info(f'Step: {self.title}')
        self.logger.info(''.ljust(50, '-'))

    def _log_sub_title(self, sub_title):
        self.logger.info('')
        self.logger.info(sub_title)
        self.logger.info(''.ljust(50, '-'))

    def _log_information(self, key, value, ljust=None, indent=0):
        if not ljust:
            ljust = len(key)
        data = "{}{}{} {}".format(''.ljust(indent), key.ljust(ljust), ':' if value!=None else '', '' if not value else value)
        self.logger.info(data)

    def _log_end(self):
        self.logger.info('')
        result = 'COMPLETED'
        if self.infos.exit_code != 0 and self.previous_exit_code == 0:
            result = 'FAILED'
        self.logger.info(f'Step Result : {result}')
        self.logger.info('')

    def bind_data(self, src):
        if not src:
            return None
        if self.infos.account_id:
            data = src.replace('{{account_id}}', self.infos.account_id)
            data = data.replace('{{accountId}}', self.infos.account_id)
            data = data.replace('{{AccountId}}', self.infos.account_id)
        if self.infos.environment:
            data = data.replace('{{environment}}', self.infos.environment)
            data = data.replace('{{Environment}}', self.infos.environment)
        if self.infos.region:
            data = data.replace('{{region}}', self.infos.region)
            data = data.replace('{{Region}}', self.infos.region)
        if self.infos.project:
            data = data.replace('{{project}}', self.infos.project)
            data = data.replace('{{Project}}', self.infos.project)
        if self.infos.service_name:
            data = data.replace('{{name}}', self.infos.service_name)
            data = data.replace('{{Name}}', self.infos.service_name)
        if self.infos.service_version:
            data = data.replace('{{version}}', self.infos.service_version)
            data = data.replace('{{Version}}', self.infos.service_version)
        if self.infos.fqdn:
            data = data.replace('{{fqdn}}', self.infos.fqdn)
            data = data.replace('{{Fqdn}}', self.infos.fqdn)
        if self.infos.external_ip:
            data = data.replace('{{external_ip}}', self.infos.external_ip)
            data = data.replace('{{externalIp}}', self.infos.external_ip)
            data = data.replace('{{ExternalIp}}', self.infos.external_ip)
        return data

    def _load_configuration(self):
        """load configuration"""
        if self.infos.configuration_file:
            with open(self.infos.configuration_file, 'r') as stream:
                result = self._normalize(yaml.safe_load(stream))
                return result
        return None

    def _normalize(self, item):
        """normalize to snake case"""
        if hasattr(item, 'keys'):
            result = {}
            for k in item.keys():
                result[self._to_snake_case(k)] = self._normalize(item[k])
            return result
        if isinstance(item, list):
            result = []
            for i in item:
                result.append(self._normalize(i))
            return result
        else:
            return item

    def _to_snake_case(self, text):
        """convert to snake case"""
        if text:
            str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()
        return None

    @abstractmethod
    def _on_execute(self):
        pass

    def wait(self, wait, label, tick=5):
        t = 0
        while (t < wait):
            time.sleep(tick)
            t += tick
            r = self.second_to_string(t)
            self.logger.info(f'{label} ... [{r} elapsed]')

    def second_to_string(self, seconds):
        tm = int(seconds)
        day = tm // (24 * 3600)
        tm = tm % (24 * 3600)
        hours = tm // 3600
        tm %= 3600
        minutes = tm // 60
        tm %= 60
        seconds = tm
        result = ''
        if day > 0:
            result += f'{day}d'
        if hours > 0:
            result += f'{day}h'
        if minutes > 0:
            result += f'{minutes}m'
        result += f'{seconds}s'
        return result

    def _generate_name(self, canary_release='', suffix=''):
        env = f'{self.infos.environment}-'
        o = None
        if len(env) > 6:
            o = slice(5)
            env = f'{self.infos.environment[o]}-'
        cr = canary_release
        if len(cr) > 2:
            o = slice(2)
            cr = cr[2:]
        o = slice(64 - (len(env) + len(cr) + len(suffix)+1))
        var = self.infos.service_name[o]
        return f'{env}{var}{suffix}-{cr}'
