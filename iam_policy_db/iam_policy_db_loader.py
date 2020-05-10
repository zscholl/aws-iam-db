from pathlib import Path

from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    core,
)


class IamPolicyDbLoader(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, table: dynamodb.Table, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        fn = _lambda.Function(
            self,
            "IamPolicyDbLoader",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="loader.handler",
            code=_lambda.Code.from_asset(
                (Path(__file__).parent.parent / "loader").as_posix()
            ),
            environment={"IamPolicyDBARN": table.table_arn},
        )
        table.grant_write_data(fn)
        daily = events.Rule(
            self, "LoadDaily", schedule=events.Schedule.rate(core.Duration.days(1))
        )
        daily.add_target(targets.LambdaFunction(fn))
