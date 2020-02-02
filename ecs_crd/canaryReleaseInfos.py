#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import uuid
import datetime
import json
import hashlib

#Attention au try/catch IOError

from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder
from ecs_crd.versionInfos import VersionInfos

class ScaleInfos:
    def __init__(self, **kwargs):
        self.desired = 2
        self.wait = 60
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class StrategyInfos:
    def __init__(self, **kwargs):
        self.weight = None
        self.wait = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class PolicyInfos:
    def __init__(self, **kwargs):
        self.name = None
        self.effect = None
        self.actions = None
        self.resources = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class StackInfos:
    def __init__(self, **kwargs):
        self.stack_id = None
        self.stack_name = None
        self.stack = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class ReleaseInfos(StackInfos):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alb_arn = None
        self.alb_dns = None
        self.alb_hosted_zone_id = None
        self.canary_release = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class FqdnInfos(object):
    def __init__(self, **kwargs):
        self.name = None
        self.hosted_zone_name = None
        self.hosted_zone_id = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class LoadBalancerInfos:
    def __init__(self, **kwargs):
        self.arn = None
        self.dns_name = None
        self.canary_release = None
        self.is_elected = False
        self.hosted_zone_id = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class ListenerRuleInfos:
    def __init__(self,  **kwargs):
        self.listener_arn = None
        self.configuration = None
        self.current_priority = 1
        self.listener_arn = None
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class SecretInfos:
    def __init__(self, **kwargs):
        self.secrets = []
        self.kms_arn = []
        self.secrets_arn = []
        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

class CanaryReleaseInfos(object):
    def __init__(self, **kwargs):
        self.id = uuid.uuid4().hex
        self.sns_topic_notification = None
        self.account_id = None
        self.action = None
        self.external_ip = None
        self.exit_code = 0
        self.exit_exception = None
        self.canary_group = None
        self.cluster_name = None
        self.cluster = None
        self.region = None
        self.environment = None
        self.project = None
        self.service_name = None
        self.service_version = None
        self.listener_port = None
        self.fqdn = []
        self.hosted_zone_id = None
        self.vpc_id = None
        self.scale_infos = None
        self.configuration_file = None
        self.strategy_infos = []
        self.init_infos = StackInfos()
        self.init_infos.stack = self._load_init_cloud_formation_template()
        self.green_infos = ReleaseInfos()
        self.green_infos.stack = self._load_green_cloud_formation_template()
        self.blue_infos = None
        self.listener_rules_infos = []
        self.secrets_infos = None
        self.elected_release = None
        self.ecs_crd_version = None

        keys = self.__dict__.keys()
        for k, v in kwargs.items():
            if k in keys:
                self.__dict__[k] = v

    def _load_green_cloud_formation_template(self):
        result = None
        filename = os.path.dirname(os.path.realpath(__file__))+'/cfn_green_release_deploy.json'
        with open(filename, 'r') as file:
            data = file.read()
            result = json.loads(data)
        result['Parameters']['Environment']['Default'] = self.environment
        result['Parameters']['Region']['Default'] = self.region
        return result

    def _load_init_cloud_formation_template(self):
        result = None
        filename = os.path.dirname(os.path.realpath(__file__))+'/cfn_init_release_deploy.json'
        with open(filename, 'r') as file:
            data = file.read()
            result = json.loads(data)
        result['Parameters']['Environment']['Default'] = self.environment
        result['Parameters']['Region']['Default'] = self.region
        return result

    def save(self):
        cache_id = f".deploy-cache/{self.id}"
        if not os.path.exists('.deploy-cache'):
            os.mkdir('.deploy-cache')
        if not os.path.exists(f"{cache_id}"):
            os.mkdir(f".deploy-cache/{self.id}")
        with open(f"{cache_id}/deploy_info.json", 'w') as file:
            file.write(json.dumps(self, cls=DefaultJSONEncoder, indent=4))

    def get_hash(self):
        data = f'{self.canary_group}#{self.service_name}#{self.environment}#{self.region}'
        hash_object = hashlib.md5(data.encode())
        return hash_object.hexdigest()
