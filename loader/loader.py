from hashlib import sha256
import json
import os
from pathlib import Path

import boto3
from policy_sentry.command.initialize import initialize


class AWSService:
    def __init__(self, data):
        self.service_name = data["service_name"]
        self.prefix = data["prefix"]
        self.actions = [AWSAction(action) for action in data["privileges"]]
        self.resources = {
            resource["resource"]: AWSResource(resource)
            for resource in data["resources"]
        }
        self.conditions = data["conditions"]

    def to_dynamo(self):
        self.dynamo_actions = []
        for action in self.actions:
            dynamo_action = {
                "action": {"S": f"{self.prefix}:{action.action}"},
                "access_level": {"S": action.access_level},
                "description": {"S": action.description},
            }
            if (
                len(action.resource_types) > 1
                and action.resource_types[0].resource_type != "*"
            ):
                dynamo_action["resources"] = {"L": self.build_dynamo_resource(action)}
            self.dynamo_actions.append(dynamo_action)

    def build_dynamo_resource(self, action):
        resources = []
        for resource in action.resource_types:
            entry = {"M": {}}
            entry["M"]["resource"] = {"S": resource.resource_type}
            entry["M"]["arn"] = {"S": self.resources[resource.resource_type].arn}
            if len(self.resources[resource.resource_type].condition_keys) > 0:
                entry["M"]["conditions"] = {
                    "SS": self.resources[resource.resource_type].condition_keys
                }
            resources.append(entry)
        return resources


class AWSAction:
    def __init__(self, data):
        self.action = data["privilege"]
        self.description = data["description"]
        self.access_level = data["access_level"]
        self.resource_types = [
            AWSResourceType(resource_type) for resource_type in data["resource_types"]
        ]


class AWSResourceType:
    def __init__(self, data):
        self.required = False
        if data["resource_type"] == "":
            self.resource_type = "*"
        else:
            self.resource_type = data["resource_type"].rstrip("*")
            if data["resource_type"][-1] == "*":
                self.required = True
        self.condition_keys = data["condition_keys"]
        self.dependent_actions = data["dependent_actions"]


class AWSResource:
    def __init__(self, data):
        self.name = data["resource"]
        self.arn = data["arn"]
        self.condition_keys = data["condition_keys"]


class AWSCondition:
    def __init__(self, data):
        self.condition = data["condition"]
        self.description = data["description"]
        self.dtype = data["type"]


def handler(event, context):
    shasum, data = refresh_data()
    stored_hash = None

    ssm = boto3.client("ssm")
    try:
        stored_hash = ssm.get_parameter(Name="iam_data_hash")["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        ssm.put_parameter(Name="iam_data_hash", Value=shasum, Type="String")

    if (
        stored_hash is not None
        and stored_hash == shasum
        and not event.get("forceupdate", False)
    ):
        print("No updates to policy data")
        exit(0)

    services = [AWSService(service) for service in data]
    update_database(services)


def refresh_data():
    initialize(None, True, True)
    with open(Path.home() / ".policy_sentry/iam-definition.json", "r") as data_file:
        hasher = sha256()
        hasher.update(data_file.read().encode("utf-8"))
        shasum = hasher.hexdigest()
        data_file.seek(0)
        return shasum, json.load(data_file)


def update_database(services):
    table_name = os.environ["IamPolicyActionsTable"]
    dynamo = boto3.client("dynamodb")
    for service in services:
        service.to_dynamo()
        for item in service.dynamo_actions:
            dynamo.put_item(TableName=table_name, Item=item)


if __name__ == "__main__":
    handler({"forceupdate": True}, None)
