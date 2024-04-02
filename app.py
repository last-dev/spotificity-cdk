#!/usr/bin/env python3

from aws_cdk import App

from src.stacks.backend_stack import BackendStack
from src.stacks.database_stack import DatabaseStack

app = App()

database_stack = DatabaseStack(app, 'DatabaseStack')
backend_stack = BackendStack(
    app,
    'BackendStack',
    monitored_artist_table=database_stack.artist_table,
)
backend_stack.add_dependency(database_stack)

app.synth()
