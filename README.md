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

#### show help

At any time on the command line, it is possible to recover the online help. To do this, simply type --help.

![alt text](_docs/help-video.gif)

#### deploy a service

To deploy a service, you must use the **deploy** sub command.The arguments for using this suborder are:




#### undeploy a service


##
