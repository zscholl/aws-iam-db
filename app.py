#!/usr/bin/env python3

from aws_cdk import core

from iam_policy_db.iam_policy_db import IamPolicyDb
from iam_policy_db.iam_policy_db_loader import IamPolicyDbLoader


app = core.App()
db_stack = IamPolicyDb(app, "iam-policy-db")
IamPolicyDbLoader(app, "iam-policy-db-loader", db_stack.table)

app.synth()
