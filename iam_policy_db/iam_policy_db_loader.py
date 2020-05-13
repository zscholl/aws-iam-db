import os
from pathlib import Path
import subprocess

from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    core,
)


class IamPolicyDbLoader(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, table: dynamodb.Table, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        layer = _lambda.LayerVersion(
            self,
            "LoaderDeps",
            code=_lambda.Code.from_asset(
                (Path(__file__).parent.parent / ".layer").as_posix()
            ),
        )
        fn = _lambda.Function(
            self,
            "IamPolicyDbLoader",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="loader.handler",
            code=_lambda.Code.from_asset(
                (Path(__file__).parent.parent / "loader").as_posix()
            ),
            environment={"IamPolicyActionsTable": table.table_name},
            layers=[layer],
            timeout=core.Duration.minutes(15),
            memory_size=512,
        )
        table.grant_write_data(fn)
        ssm_policy = iam.PolicyStatement(
            actions=["ssm:GetParameter", "ssm:PutParameter"],
            effect=iam.Effect.ALLOW,
            resources=["arn:aws:ssm:us-east-2:947245232016:parameter/iam_data_hash"],
        )
        fn.add_to_role_policy(ssm_policy)
        daily = events.Rule(
            self, "LoadDaily", schedule=events.Schedule.rate(core.Duration.days(1))
        )
        daily.add_target(targets.LambdaFunction(fn))

    def create_dependencies_layer(
        self, requirements_path: str, output_dir: str
    ) -> _lambda.LayerVersion:
        # Install requirements for layer
        if not os.environ.get("SKIP_PIP"):
            subprocess.check_call(
                # Note: Pip will create the output dir if it does not exist
                f"pip install -r {requirements_path} -t {output_dir}/python".split()
            )
        return
