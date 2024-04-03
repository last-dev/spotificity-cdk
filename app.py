#!/usr/bin/env python3
from dataclasses import fields
from os import environ

from aws_cdk import App, Environment

from src.constants import Accounts, AwsAccount
from src.helpers.helpers import generate_name
from src.stacks.backend_stack import BackendStack
from src.stacks.database_stack import DatabaseStack

# Explicitly pull env info so account ID is set now, as oppose to being
# determined at deployment w/ CloudFormation's intrinsic {"Ref":"AWS::AccountId"}
env = Environment(account=environ['CDK_DEFAULT_ACCOUNT'], region=environ['CDK_DEFAULT_REGION'])
app = App()

for field in fields(Accounts):
    stage = field.name
    account: AwsAccount = getattr(Accounts, stage)
    if env.account == account.account_id:
        account_props = account

        database_stack = DatabaseStack(
            app, generate_name('DatabaseStack', account_props), account=account_props
        )
        backend_stack = BackendStack(
            app,
            generate_name('BackendStack', account_props),
            account=account_props,
            artist_table=database_stack.artist_table,
        )
        backend_stack.add_dependency(database_stack)

app.synth()
