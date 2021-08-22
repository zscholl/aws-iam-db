#!/usr/bin/env python3

from aws_iam_db.build_db import init
from aws_iam_db.docs import get_docs
import typer


def run(json_path: str = "/tmp/actions_data.json", db_path: str = "iam.db"):
    get_docs(json_path)
    init(json_path, db_path)


def main():
    typer.run(run)
