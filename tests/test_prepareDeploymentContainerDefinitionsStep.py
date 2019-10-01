import pytest
from unittest.mock import MagicMock
import logging

from ecs_crd.canaryReleaseInfos import CanaryReleaseInfos
from ecs_crd.prepareDeploymentContainerDefinitionsStep import PrepareDeploymentContainerDefinitionsStep
from ecs_crd.canaryReleaseInfos import ScaleInfos

logger = logging.Logger('mock')
infos = CanaryReleaseInfos(action='test')
step = PrepareDeploymentContainerDefinitionsStep(infos, logger)

def test_process_container_name_valid():
    # default
    source = {}
    target = {}
    step._process_container_name(source, target)
    target['Name'] == 'default'
    # with name
    source = {}
    source['name']='test'
    target = {}
    step._process_container_name(source, target)
    target['Name'] == source['name']

def test_process_container_name_valid():
    
    # default
    source = {}
    target = {}
    step.infos.account_id='123456789'
    step.infos.region='eu-west-3'
    step.infos.service_name='service'
    step.infos.service_version='latest'

    step._process_container_image(source, target)
    assert target['Image'] == '123456789.dkr.ecr.eu-west-3.amazonaws.com/service:latest'

    # with name
    source = {}
    source['image']='test'
    target = {}
    step._process_container_image(source, target)
    assert target['Image'] == source['image']

def test_process_container_cpu_invalid():
    source = {}
    source['cpu'] = 'a'
    target = {}
    with pytest.raises(ValueError):
        step._process_container_cpu(source, target)

def test_process_container_cpu_valid():
    source = {}
    target = {}
    
    # default value
    step._process_container_cpu(source, target)
    assert target['Cpu'] == 128 
    
    # set value
    source['cpu'] = 256
    target = {}
    step._process_container_cpu(source, target)
    assert target['Cpu'] == source['cpu']  

def test_process_container_entry_point_valid():
     source = {}
     source['entry_point']=[]
     source['entry_point'].append('a')
     source['entry_point'].append('b')
     target = {}
     step._process_container_entry_point(source, target)
     assert target['EntryPoint'] == 'a,b'

def test_process_container_entry_point_invalid():
     source = {}
     source['entry_point']='a'
     target = {}
     with pytest.raises(ValueError):
        step._process_container_entry_point(source, target)

def test_process_container_command_valid():
     source = {}
     source['command']=[]
     source['command'].append('a')
     source['command'].append('b')
     target = {}
     step._process_container_command(source, target)
     assert len(target['Command'])==2
     assert target['Command'][0] == 'a'
     assert target['Command'][1] == 'b'

def test_process_container_command_invalid():
     source = {}
     source['command']='b'
     target = {}
     with pytest.raises(ValueError):
        step._process_container_command(source, target)
   
def test_process_container_dns_search_domains_valid():
     source = {}
     source['dns_search_domains']=[]
     source['dns_search_domains'].append('a')
     source['dns_search_domains'].append('b')
     target = {}
     step._process_container_dns_search_domains(source, target)
     assert len(target['DnsSearchDomains'])==2
     assert target['DnsSearchDomains'][0] == 'a'
     assert target['DnsSearchDomains'][1] == 'b'

def _process_container_dns_search_domains_invalid():
     source = {}
     source['dns_search_domains']='b'
     target = {}
     with pytest.raises(ValueError):
        step._process_container_dns_search_domains(source, target)


def test_process_container_disable_networking_valid():
     source = {}
     source['disable_networking'] = True
     target = {}
     step._process_container_disable_networking(source, target)
     assert target['DisableNetworking'] == source['disable_networking']
     source = {}
     source['disable_networking'] = False
     target = {}
     step._process_container_disable_networking(source, target)
     assert target['DisableNetworking'] == source['disable_networking']

def _process_container_disable_networking_invalid():
     source = {}
     source['disable_networking']='b'
     target = {}
     with pytest.raises(ValueError):
        step._process_container_disable_networking(source, target)

def test_process_container_dns_servers_valid():
     source = {}
     source['dns_servers']=[]
     source['dns_servers'].append('a')
     source['dns_servers'].append('b')
     target = {}
     step._process_container_dns_servers(source, target)
     assert len(target['DnsServers'])==2
     assert target['DnsServers'][0] == 'a'
     assert target['DnsServers'][1] == 'b'

def _process_container_dns_servers_invalid():
     source = {}
     source['dns_servers']='b'
     target = {}
     with pytest.raises(ValueError):
        step._process_container_dns_servers(source, target)
   

def test_process_container_start_timeout_invalid():
    source = {}
    source['start_timeout'] = 'a'
    target = {}
    with pytest.raises(ValueError):
        step._process_container_start_timeout(source, target)

def test_process_container_start_timeout_valid():
    source = {}
    source['start_timeout']=60
    target = {}
    
    step._process_container_start_timeout(source, target)
    assert target['StartTimeout'] ==  source['start_timeout']

def test_process_container_stop_timeout_invalid():
    source = {}
    source['stop_timeout'] = 'a'
    target = {}
    with pytest.raises(ValueError):
        step._process_container_stop_timeout(source, target)

def test_process_container_stop_timeout_valid():
    source = {}
    source['stop_timeout']=60
    target = {}
    
    step._process_container_stop_timeout(source, target)
    assert target['StopTimeout'] == source['stop_timeout']
    
def test_process_container_hostname_valid():
    source = {}
    source['hostname']='a'
    target = {}
    
    step._process_container_hostname(source, target)
    assert target['Hostname'] ==  source['hostname']
    