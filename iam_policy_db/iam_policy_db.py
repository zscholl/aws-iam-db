from aws_cdk import aws_dynamodb as dynamodb, core


class IamPolicyDb(core.Stack):
    @property
    def table(self):
        return self._table

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self._table = dynamodb.Table(
            self,
            "IamPolicy",
            partition_key=dynamodb.Attribute(
                name="action", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )
