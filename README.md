# AWS ECS Canary Release Deploy Command Line

## I - Introduction

The implementation of Zero Downtime Deployment is based on a number of patterns and best practices.

This project aims to provide a tool that runs on console to deploy ECS services using the concepts of canary release and blue/green deployment.

### I.1 - Pattern / Concept

#### I.1.2 Blue/Green deployment

#### I.1.2 Canary deployment

### I.2 - Prerequistes

## II - How is deployment done ?

![alt text](_docs/state-machine.png)

## III - Installation

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

## IV - Usage

### IV.1 - How use the command line ?

#### IV.1.1 - Show help

At any time on the command line, it is possible to recover the online help. To do this, simply type --help.

![alt text](_docs/help-video.gif)

#### IV.1.2 Deploy a service

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

#### IV.1.3 Undeploy a service

To undeploy a service, you must use the **undeploy** sub command. The arguments for using this suborder are the same as for the suborder **deploy**.

## V - Decribe deployment file

The description file of a deployment is file in yml format. The format of this file is the following.

### V.1 - canary tag

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

#### V.1.1 - canary.group

**description** : Information about selecting the application load balancer group used for service deployment. The **group** tag is used to identify which application load balancer group the service should deploy to. ( show AWS Application Load Balancer Tags **CanaryGroup** )

**type**: string

**optional** : false

#### V.1.2 - canary.releases

Information about selecting the application load balancer group used for service deployment. The **release** tag identifies the two application load balancers. The values for blue and green are **CanaryRelease** labels on application load balancers.

##### V.1.2.1 - canary.releases.blue

**description** : Identifier of the first application load balancer

**type**: string

**optional** : false

##### V.1.2.2 - canary.releases.green

**description** : Identifier of the second application load balancer

**type**: string

**optional** : false

![alt text](_docs/deploy.canary.group.png)

#### V.1.3 - canary.scale

Information about scaling the service for deployment.

#### V.1.3.1 - canary.scale.wait

**description** : Waiting time after scaling the number of service intances in the cluster

**type** : integer

**default** : 60

**optional** : true

#### V.1.3.2 - canary.scale.desired

**description** : The Number of desired instances of the service in the cluster

**type**: integer

**default** : 2

**optional** : true

#### V.1.3.2 - canary.strategy

Contains the definition of the service deployment strategy. A deployment strategy is composed of state that allows changing the distribution of DNS weights between application load balancers. If during deployment of the service the new version of the service is considered as invalid, the deployment is canceled and a rollback is performed.

<table>
    <tr>
        <td>
            <strong>Deployment succed</strong>
        </td>
                <td>
            <strong>Deployment failed</strong>
        </td>
    <tr>
    <tr>
        <td>
            <img src='_docs/canary_release_ok.png'>
        </td>
        <td>
            <img src='_docs/canary_release_ko.png'>
        </td>
    </tr>
<table>


