---
description: Terraform instructions
---

# Terraform

## Structure

- data sources should be placed in `data.tf`
- providers and versions should be placed in `terraform.tf`
- variables should be placed in `variables.tf`
- outputs should be placed in `outputs.tf`

Resources should be grouped in files which are based on their name. For example:

- IAM policies should be placed in `iam-policies.tf`
- IAM roles should be placed in `iam-roles.tf`
- KMS keys should be placed in `kms-keys.tf`
- locals should be placed in `locals.tf`

- modules should be placed in `modules/`

## Naming

- Resources should be named using snake_case. For example:
  `resource "aws_iam_role" "example_role_name" {}`

- Resource names should not repeat the resource type. For example:

  Preferred:
  `resource "aws_iam_role" "example_role_name" {}`
  Avoid:
  `resource "aws_iam_role" "example_role_name_role" {}`

- Modules should be named using snake_case. For example:
  `module "example_module_name" {}`

- Module names should be descriptive of their purpose. For example:
  `module "example_iam_role" {}`

## Conventions

- Where possible, use modules from the [terraform-aws-modules namespace](https://registry.terraform.io/namespaces/terraform-aws-modules). If this is not possible, notify the user and proceed.
- Always reference Terraform modules using a Git source pinned to a full commit SHA via the ref parameter, not a branch or tag
