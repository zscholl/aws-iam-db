#!/usr/bin/env python3

from aws_cdk import core

from iam_policy_db.iam_policy_db_stack import IamPolicyDbStack


app = core.App()
IamPolicyDbStack(app, "iam-policy-db")

app.synth()
