#!/usr/bin/env python3
import codecs
import os.path
import re
import sys
from ecs_crd.versionInfos import VersionInfos

from setuptools import setup, find_packages

version_infos = VersionInfos()

setup (
    name = 'ecs-crd-cli',
    author = "Adventiel",
    author_email = "gwendall.garnier.fr@gmail.com",
    include_package_data = True,
    version = version_infos.version,
    description= version_infos.description,
    url='https://github.com/AdventielFr/ecs-crd-cli.git',
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6"
    ],
    install_requires = [
        'bleach==3.1.0',
        'boto3==1.9.220',
        'botocore==1.12.220',
        'certifi==2019.6.16',
        'chardet==3.0.4',
        'Click==7.0',
        'docutils==0.15.2',
        'humanfriendly==4.18',
        'idna==2.8',
        'jmespath==0.9.4',
        'pkginfo==1.5.0.1',
        'Pygments==2.4.2',
        'python-dateutil==2.8.0',
        'PyYAML==5.1.2',
        'readme-renderer==24.0',
        'requests==2.22.0',
        'requests-toolbelt==0.9.1',
        's3transfer==0.2.1',
        'six==1.12.0',
        'termcolor==1.1.0',
        'tqdm==4.35.0',
        'urllib3==1.25.3',
        'webencodings==0.5.1'
    ],
    packages = find_packages(exclude=["tests/*"]),
    package_data = {'': ['ecs_crd/cfn_*_release_deploy.json']},
    scripts = [
        'bin/ecs-crd'
    ]
)