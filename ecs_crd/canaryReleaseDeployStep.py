#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import logging
import yaml
import time
import datetime
import re
import boto3
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

    def _to_int(self, val):
        try:
            return int(val)
        except:
            return None

    def _process_property(self, **kwargs):
        origin = None
        source = None
        source_property = None
        target_property = None
        parent_property = None
        type = None
        pattern = None
        required = False
        multi = False
        default = None
        indent = 0
        
        for k,v in kwargs.items():
            if k == 'source':
                source = v
            if k == 'target':
                target = v
            if k == 'source_property':
                source_property = v
            if k == 'target_property':
                target_property = v
            if k == 'type':
                type = v
            if k == 'pattern':
                pattern = v
            if k == 'required':
                required = bool(v)
            if k == 'default':
                default = v
            if k == 'indent':
                indent = int(v)
            if k == 'parent_property':
                parent_property = v
            if k == 'multi':
                multi = bool(v)
        
        if not target_property:
            target_property = self._to_pascal_case(source_property)
        
        if default and source_property not in source:
            source[source_property] = default
        
        suffix_message = '.'
        if parent_property:
            suffix_message = f' for {parent_property}.'

        if source_property in source:
            if type:
                if isinstance(source[source_property], type):
                    target[target_property] = source[source_property]
                else:
                    raise ValueError(f'{target_property}: {source[source_property]} is not valid{suffix_message}')
            else:
                target[target_property] = self._bind_data(source[source_property])
            if pattern:
                val = re.match(pattern, target[target_property])
                if not val:
                    raise ValueError(f'{target_property}: {source[source_property]} is not valid{suffix_message}')
            self._log_information(key = ('- ' if multi else '' )+target_property, value=target[target_property] , indent=indent)
        else:
            if required:
                raise ValueError(f'{target_property} is required{suffix_message}')

    def _bind_data_fqdn(self, source):
        try:
            result = source
            match = re.match('.*({{fqdn(\\[(\\d)\\])*}}).*',source)
            while match != None:
                if match.groups()[2]:
                    index = int(match.groups()[2])
                    pattern = str(match.groups()[0])
                    result = result.replace(pattern, self.infos.fqdn[index].name)
                else:
                    result = result.replace(str(match.groups()[0]),self.infos.fqdn[0].name)
                match = re.match('.*({{fqdn(\\[(\\d)\\])*}}).*',result)
            return result
        except:
            raise ValueError('Invalid Fqdn template :{}'.format(source))

    def _bind_data(self, source):
        if not source:
            return None
        data = source
        if self.infos.account_id:
            data = data.replace('{{account_id}}', self.infos.account_id)
        if self.infos.environment:
            data = data.replace('{{environment}}', self.infos.environment)
        if self.infos.region:
            data = data.replace('{{region}}', self.infos.region)
        if self.infos.project:
            data = data.replace('{{project}}', self.infos.project)
        if self.infos.service_name:
            data = data.replace('{{name}}', self.infos.service_name)
        if self.infos.service_version:
            data = data.replace('{{version}}', self.infos.service_version)
        if self.infos.external_ip:
            data = data.replace('{{external_ip}}', self.infos.external_ip)
        data = self._bind_data_fqdn(data)
        return data

    def _load_configuration(self):
        """load configuration"""
        if self.infos.configuration_file:
            with open(self.infos.configuration_file, 'r') as stream:
                return yaml.safe_load(stream)
        return None

    def _to_snake_case(self, text):
        """convert to snake case"""
        if text:
            str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()
        return None

    def _to_pascal_case(self,text):
        result = None
        if not text:
            return result
        s = text.split('_')
        return ''.join(map(lambda i: i.capitalize(),s ))

    @abstractmethod
    def _on_execute(self):
        pass

    def _wait(self, wait, label, tick=5):
        t = 0
        while (t < wait):
            time.sleep(tick)
            t += tick
            r = self._second_to_string(t)
            self.logger.info(f'{label} ... [{r} elapsed]')

    def _second_to_string(self, seconds):
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
