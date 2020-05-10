import json
import os

import boto3
from policy_sentry.command.initialize import initialize


class AWSService:
    def __init__(self, data):
        self.service_name = data["service_name"]
        self.prefix = data["prefix"]
        self.actions = [AWSAction(action) for action in data["privileges"]]
        self.resources = [AWSResource(resource) for resource in data["resources"]]
        self.conditions = data["conditions"]


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



class AWSResource():
    def __init__(self, data):
        self.name = data['resource']
        self.arn = data['arn']
        self.condition_keys = data['condition_keys']


class AWSCondition():
    def __init__(self, data):
        self.condition = data['condition']
        self.description = data['description']
        self.dtype = data['type']

def handler(event, context):
    table_arn = os.environ["IamPolicyDBARN"]
    data = refresh_data()
    services = [AWSService(service) for service in data]
    print("foo")

def refresh_data():
    #initialize(None, True, True)
    with open("~/.policy_sentry/iam-definition.json", "r") as data_file:
        return json.load(data_file)


if __name__ == "__main__":
    handler(None, None)