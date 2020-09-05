# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[see reference](references/snake_case_reference.yml).

## [1.1.0] - 2020-05-08
### Added

 - feat : healtcheck on container for dependencies

 - feat : add log configuration definition

 - feat: add dry-run sub command for ecs-crd


## [1.0.0] - 2020-11-04
### Added

 - feat : multi rules on listener ( oidc / cognito / fixed-reponse / redirect )


## [0.50.2] - 2019-11-04
### Added

- fix : check exist container image in AWS ECR before creation cloudformation stack.

## [0.50.1] - 2019-10-16
### Added

- fix: find cloud formation when more one hundred cloudformation stack

## [0.20.1] - 2019-10-09
### Added

- fix: error prepareDeploymentServiceDefinitionStep.py / prep_process_placement_constraints_contraint_expression / source

## [0.20.0] - 2019-10-09
### Added

- multi fqdn management ( allow array or one string for fqdn )

## [Unreleased]

## [0.17.0] - 2019-10-02
### Added

- new command 'validate' for check deployment file
- Documentation for use topic notification sns.
- bugfix: Consideration of deployment error cases by the notification process sns.
