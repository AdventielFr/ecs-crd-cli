# AWS ECS Canary Release Deploy Command Line

## Introduction

The implementation of Zero Downtime Deployment is based on a number of patterns and best practices.

This project aims to provide a tool that runs on console to deploy ECS services using the concepts of canary release and blue/green deployment.

### Pattern / Concept

#### Blue/Green deployment



### Prerequistes

## How is deployment done ?

### Used DNS Weight feature of AWS Route 53

### 

## Installation

To install the command line tool, simply install it using pip.

```
pip install ecs-crd-cli
```

One of the best practices and do it using a virtualenv.

```
virtualenv -p python3 my-project
source my-project/bin/activate
pip install ecs-crd-cli
```

![alt text](_docs/install-video.gif)

## Usage

### How use the command line ?

#### Show help

At any time on the command line, it is possible to recover the online help. To do this, simply type --help.

![alt text](_docs/help-video.gif)

#### deploy a service

To deploy a service, you must use the **deploy** sub command.The arguments for using this suborder are:

| Argument (long) | Argument ( short) | Description  |
|:---|:----|:-----|
| --help | | documentation of sub command|
| --environment | -e | the environment to deploy ( the allowed values ​​are dev, qua, stage, preprod, prod ) |
| --region | -r | aws region to deploy the service |
| --configuration-file | -f | configuration file .yml use to describe the deployment|
| --configuration-dir | -d | configuration directory, if configuration-file is not set |
| --verbose | | increase the level of trace verbosity|
| --log-file | | name of the file where the traces will be written |

* If you use the **--configuration-file** argument, you do not need to fill in the --configuration-dir argument.

* If you use the **--configuration-dir** argument, the tool will look in the directory for a file of type **environment**.deploy.yml

#### undeploy a service

To undeploy a service, you must use the **un-deploy** sub command. The arguments for using this suborder are the same as for the suborder **deploy**.

### Decribe deployment file

The description file of a deployment is file in yml format. The format of this file is the following.

#### canary tag

The "canary" tag contains the definition of the deployment strategy.

```
canary:
  group: private
  releases:
    blue: 1
    green: 2
  scale:
    wait: 60
  strategy:
    - weight: 50
      wait: 60
```

##### canary.group & canary.releases

The group tag is used to identify which application load balancer group the service should deploy to. ( show AWS Application Load Balancer Tags **CanaryGroup** )

The release tag identifies the two application load balancers. The values for blue and green are **CanaryRelease** labels on application load balancers

![alt text](_docs/deploy.canary.group.png)
