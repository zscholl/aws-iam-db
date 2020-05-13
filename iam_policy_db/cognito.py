from aws_cdk import (
    aws_cognito as cognito,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    core,
)


class DbAccess(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, table: dynamodb.Table, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        pool = cognito.CfnIdentityPool(
            self, "DbIdentityPool", allow_unauthenticated_identities=True
        )
        pool_unauth_role = iam.Role(
            self,
            "DbReadRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {"cognito-identity.amazonaws.com:aud": pool.ref},
                    "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "unauthenticated"}
                },
            ),
        )
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            "RoleAttachments",
            identity_pool_id=pool.ref,
            roles={"unauthenticated": pool_unauth_role.role_arn},
        )
        table.grant_read_data(pool_unauth_role)
