from hashlib import sha256
import json
import os
from pathlib import Path
import logging
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from policy_sentry.shared import constants

constants.CONFIG_DIRECTORY = "/tmp/.policy_sentry"
constants.LOCAL_DATASTORE_FILE_PATH = "/tmp/.policy_sentry/iam-definition.json"
constants.LOCAL_ACCESS_OVERRIDES_FILE = "/tmp/.policy_sentry/access-level-overrides.yml"
constants.LOCAL_HTML_DIRECTORY_PATH = "/tmp/.policy_sentry/data/docs"

from policy_sentry.command.initialize import initialize

logger = logging.getLogger("DBLoader")
logger.setLevel(logging.INFO)


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
    
    def to_json(self):
        actions = []
        for action in self.actions:
            item = {
                "id": action.uuid,
                "action": f"{self.prefix}:{action.action}",
                "access_level": action.access_level,
                "service_name": self.service_name
            }
            if (
                len(action.resource_types) >= 1
                and action.resource_types[0].resource_type != "*"
            ):
                item["resources"] = self.build_resources(action)
            if action.description:
                item["description"] = action.description
            actions.append(item)
        return actions
    
    def build_resources(self, action):
        resources = []
        for resource in action.resource_types:
            entry = {}
            entry["resource"] = resource.resource_type
            entry["arn"] = self.resources[resource.resource_type].arn if resource.resource_type != '*' else '*'
            if resource.resource_type != '*' and len(self.resources[resource.resource_type].condition_keys) > 0:
                entry["conditions"] =  self.resources[resource.resource_type].condition_keys
            resources.append(entry)
        # remove * resource if others exist
        # TODO: conditions aren't being parsed into the object for S3
        return_list = []
        if len(resources) > 1:
            conditions = None
            for resource in resources:
                if resource["arn"] != "*":
                    return_list.append(resource)
                if "conditions" in resource:
                    # there's an edge case where some resources allow condition keys
                    # but AWS only lists them in the blank row. So we need to do this
                    # to keep conditions on the more specific resource
                    conditions = resource["conditions"]
            if conditions and len(return_list) == 1:
                return_list[0]["conditions"] = conditions
            return return_list
        return resources

    def to_dynamo(self):
        self.dynamo_actions = []
        for action in self.actions:
            dynamo_action = {
                "id": {"S": action.uuid},
                "action": {"S": f"{self.prefix}:{action.action}"},
                "access_level": {"S": action.access_level},
                "service_name": {"S": self.service_name}
            }
            if (
                len(action.resource_types) >= 1
                and action.resource_types[0].resource_type != "*"
            ):
                dynamo_action["resources"] = {"L": self.build_dynamo_resource(action)}
            if action.description:
                dynamo_action["description"] = {"S": action.description}
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
        self.uuid = str(uuid4())
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
    logger.info(f"Data has hash {shasum}")
    stored_hash = None

    ssm = boto3.client("ssm")
    try:
        stored_hash = ssm.get_parameter(Name="iam_data_hash")["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        logger.info("Parameter not found. Initializing")
        ssm.put_parameter(Name="iam_data_hash", Value=shasum, Type="String")

    if (
        stored_hash is not None
        and stored_hash == shasum
        and not event.get("forceupdate", False)
    ):
        print("No updates to policy data, exiting")
        exit(0)

    services = [AWSService(service) for service in data]
    update_database(services)
    ssm.put_parameter(Name="iam_data_hash", Value=shasum, Type="String", Overwrite=True)


def refresh_data():
    initialize(None, True, True)
    with open("/tmp/.policy_sentry/iam-definition.json", "r") as data_file:
        hasher = sha256()
        hasher.update(data_file.read().encode("utf-8"))
        shasum = hasher.hexdigest()
        data_file.seek(0)
        return shasum, json.load(data_file)


def update_database(services):
    table_name = os.environ["IamPolicyActionsTable"]
    dynamo = boto3.client("dynamodb")
    for service in services:
        logger.info(f"Updating service {service.service_name}")
        service.to_dynamo()
        for item in service.dynamo_actions:
            try:
                dynamo.put_item(TableName=table_name, Item=item)
            except ClientError:
                logger.error(f"Unable to put item: {item}", exc_info=True)


if __name__ == "__main__":
    with open("/tmp/.policy_sentry/iam-definition.json", "r") as data_file:
        data = json.load(data_file)
    services = [AWSService(service) for service in data]

    actions = []
    for service in services:
        actions.extend(service.to_json())
    with open("actions.json", "w") as out_file:
        json.dump(actions, out_file)