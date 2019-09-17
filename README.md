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

### V.1 - canary tag definition

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
    - weight: 10
      wait: 70
    - weight: 60
      wait: 50

```

#### V.1.1 - canary.group

**description** : Information about selecting the application load balancer group used for service deployment. The **group** tag is used to identify which application load balancer group the service should deploy to. ( show AWS Application Load Balancer Tags **CanaryGroup** )

**type**: string

**optional** : false

#### V.1.2 - canary.releases

Information about selecting the application load balancer group used for service deployment. The **release** tag identifies the two application load balancers. The values for blue and green are **CanaryRelease** labels on application load balancers.

##### V.1.2.1 - canary.releases.blue

&nbsp;&nbsp;**description** : Identifier of the first application load balancer

&nbsp;&nbsp;**type**: string

&nbsp;&nbsp;**optional** : false

##### V.1.2.2 - canary.releases.green

&nbsp;&nbsp;**description** : Identifier of the second application load balancer

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : false

![alt text](_docs/deploy.canary.group.png)

#### V.1.3 - canary.scale

Information about scaling the service for deployment.

#### V.1.3.1 - canary.scale.wait

&nbsp;&nbsp;**description** : Waiting time after scaling the number of service intances in the cluster

&nbsp;&nbsp;**type** : integer

&nbsp;&nbsp;**default** : 60

&nbsp;&nbsp;**optional** : true

#### V.1.3.2 - canary.scale.desired

&nbsp;&nbsp;**description** : The Number of desired instances of the service in the cluster

&nbsp;&nbsp;**type**: integer

&nbsp;&nbsp;**default** : 2

&nbsp;&nbsp;**optional** : true

#### V.1.3.2 - canary.strategy

Contains the definition of the service deployment strategy. A deployment strategy is composed of state that allows changing the distribution of DNS weights between application load balancers.

If during deployment of the service the new version of the service is considered as invalid, the deployment is canceled and a rollback is performed.

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

each of item of stategy is composed of

#### V.1.3.2.1 - canary.strategy.weight

&nbsp;&nbsp;**description** : The weight for DNS of green application load balancers.

&nbsp;&nbsp;**type** : integer

&nbsp;&nbsp;**optional** : false

#### V.1.3.2.1 - canary.strategy.wait

&nbsp;&nbsp;**description** : The timeout period before testing the different health checks for target groups associated with the green application load balancer.

&nbsp;&nbsp;**type** : integer

&nbsp;&nbsp;**optional** : false

Example of deployment strategy

![alt text](_docs/strategy-step.png)

### V.2 - service tag definition

The "service" tag contains the definition of the service to deploy. The definition is very similar to the statement of an ECS service by AWS cloud formation

```
service:
  project: ...
  name: ...
  cluster: ...
  fqdn: ...
  version: ...
  scheduling_strategy: ...
  platform_version: ...
  placement_constraints: ...
  placement_strategies: ...
  containers: ...
  policies: ...
```

#### V.2.1 - service.**project**

&nbsp;&nbsp;**description** : The project name. Once the value is filled you can use the **{{project}}** template for the other properties.

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : false

#### V.2.2 - service.name

&nbsp;&nbsp;**description** : The service name. Once the value is filled you can use the **{{name}}** template for the other properties.

&nbsp;&nbsp;**type**: string

&nbsp;&nbsp;**optional** : false

#### V.2.3 - service.cluster

&nbsp;&nbsp;**description** : ECS cluster name where the service is to be deployed.

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : false

#### V.2.4 - service.fqdn

&nbsp;&nbsp;**description** : Fully qualified domain name of the service to register in AWS Route 53 domain. Once the value is filled you can use the **{{fqdn}}** template for the other properties.

&nbsp;&nbsp;**type**  string

&nbsp;&nbsp;**optional** : false

#### V.2.5 - service.version

&nbsp;&nbsp;**description** : Version of the service. Once the value is filled you can use the **{{fqdn}}** template for the other properties.

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : false

#### V.2.6 - service.scheduling_strategy

&nbsp;&nbsp;**description** : The scheduling strategy to use for the service. For more information [see AWS documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ecs-service.html#cfn-ecs-service-schedulingstrategy)

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : true

#### V.2.7 - service.platform_version

&nbsp;&nbsp;**description** : The platform version that your tasks in the service are running on. A platform version is specified only for tasks using the Fargate launch type. If one isn't specified, the LATEST platform version is used by default. For more information [see AWS documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ecs-service.html#cfn-ecs-service-platformversion)

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : true

#### V.2.8 - service.placement_constraints

&nbsp;&nbsp;**description** : An array of placement constraint objects to use for tasks in your service. For more information [see AWS documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ecs-service.html#cfn-ecs-service-placementconstraints)

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : true

#### V.2.9 - service.placement_strategies

&nbsp;&nbsp;**description** : The placement strategy objects to use for tasks in your service. For more information [see AWS documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ecs-service.html#cfn-ecs-service-placementstrategies)

&nbsp;&nbsp;**optional** : true

#### V.2.9 - service.containers

&nbsp;&nbsp;**description** : The list of container defintitions. For more information see ( container tag definition V.3 )

&nbsp;&nbsp;**type** : container tag definition

&nbsp;&nbsp;**optional** : false

### V.3 - container tag definition

The "container" tag contains the definition of containers to deploy. The definition is very similar to the statement of an ECS task definition by AWS cloud formation

```
service:
  containers:
    - name: ...
      image: ...
      cpu: ...
```

#### V.3.1 - container.name

&nbsp;&nbsp;**description** : The name of container in the service.

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**optional** : true

&nbsp;&nbsp;**default** : "default"

#### V.3.2 - container.image

&nbsp;&nbsp;**description** : The docker image to deploy. If the value is not filled in, the value will be **{{account_id}}**.dkr.ecr.**{{region}}**.Amazonaws.com/**{{name}}**:**{{version}}**

with,

* {{account_id}} : aws account owner

* {{region}} : Aws region to deploy the service ( see IV.1.2 argument Command LIne )

* {{name}} : Name of service to deploy ( see V.2.2 )

* {{version}} : Version of service to deploy ( see V.2.5 )

&nbsp;&nbsp;**optional** : true

&nbsp;&nbsp;**type** : string

&nbsp;&nbsp;**default** : default

#### V.3.3 - container.cpu

**description** : The number of cpu units used by the task. For more information [see AWS documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ecs-taskdefinition.html#cfn-ecs-taskdefinition-cpu)

&nbsp;&nbsp;**optional** : true

&nbsp;&nbsp;**type** : integer

&nbsp;&nbsp;**default** : 128

### V.2 - target_group tag


### V.3 - listener tag