#!/usr/bin/env python3
import os
import aws_cdk as cdk
from one_app.one_app_stack import OneAppStack
import one_app.aspect as _aspects

_app = cdk.App()
_env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])
_stack_name = _app.node.try_get_context("product_name")

#print(_stack_name)
OneAppStack(_app, _stack_name,
    synthesizer=cdk.DefaultStackSynthesizer(
        # ARN of the role assumed by the CLI and Pipeline to deploy here
            #deploy_role_arn="arn:${AWS::Partition}:iam::${AWS::AccountId}:role/pm-cdk-${Qualifier}-deploy-role-${AWS::AccountId}-${AWS::Region}",
        # ARN of the role used for file asset publishing (assumed from the deploy role)
            #file_asset_publishing_role_arn="arn:${AWS::Partition}:iam::${AWS::AccountId}:role/pm-cdk-${Qualifier}-file-publishing-role-${AWS::AccountId}-${AWS::Region}",
        # ARN of the role used for Docker asset publishing (assumed from the deploy role)
            #image_asset_publishing_role_arn="arn:${AWS::Partition}:iam::${AWS::AccountId}:role/pm-cdk-${Qualifier}-image-publishing-role-${AWS::AccountId}-${AWS::Region}",
        # ARN of the role passed to CloudFormation to execute the deployments
            #cloud_formation_execution_role="arn:aws:iam::${AWS::AccountId}:role/CloudFormationExecutionRole"
        ),
    env=_env,

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

cdk.Aspects.of(_app).add(_aspects.PactRoleName())
_app.synth()
