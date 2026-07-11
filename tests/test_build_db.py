"""Tests for the action -> condition-key association added to the schema.

AWS documents condition keys per (action, resource type) row in its "Actions"
table. Some actions operate on no resource type (e.g. acm:RequestCertificate)
and carry their condition keys on a blank-resource-type row, so the keys have to
be read from the action rows directly rather than through resource types.
"""

from sqlalchemy import text

from aws_iam_db.build_db import Base, connect, create_database, normalize_condition_key


# A single-service fixture shaped exactly like the scraper's JSON output. The
# ACM "RequestCertificate" action deliberately has an empty resource type, which
# is where its action-level condition keys live.
ACM_FIXTURE = [
    {
        "service_name": "AWS Certificate Manager",
        "prefix": "acm",
        "conditions": [
            {"condition": "acm:DomainNames", "description": "domains", "type": "ArrayOfString"},
            {"condition": "acm:ValidationMethod", "description": "validation", "type": "String"},
            {"condition": "acm:KeyAlgorithm", "description": "algorithm", "type": "String"},
            {"condition": "aws:RequestTag/${TagKey}", "description": "request tag", "type": "String"},
            {"condition": "aws:TagKeys", "description": "tag keys", "type": "ArrayOfString"},
            {"condition": "aws:ResourceTag/${TagKey}", "description": "resource tag", "type": "String"},
        ],
        "resources": [
            {
                "resource": "certificate",
                "arn": "arn:${Partition}:acm:${Region}:${Account}:certificate/${CertificateId}",
                "condition_keys": ["aws:ResourceTag/${TagKey}"],
            }
        ],
        "privileges": [
            {
                "privilege": "RequestCertificate",
                "description": "Request a certificate",
                "access_level": "Write",
                "resource_types": [
                    {
                        "resource_type": "",
                        "condition_keys": [
                            "acm:DomainNames",
                            "acm:ValidationMethod",
                            "acm:KeyAlgorithm",
                            "aws:RequestTag/${TagKey}",
                            "aws:TagKeys",
                        ],
                        "dependent_actions": [],
                    }
                ],
            },
            {
                "privilege": "AddTagsToCertificate",
                "description": "Add tags",
                "access_level": "Tagging",
                "resource_types": [
                    {
                        "resource_type": "certificate",
                        "condition_keys": ["aws:RequestTag/${TagKey}", "aws:TagKeys"],
                        "dependent_actions": [],
                    }
                ],
            },
            {
                "privilege": "DescribeCertificate",
                "description": "Describe a certificate",
                "access_level": "Read",
                "resource_types": [
                    {"resource_type": "certificate", "condition_keys": [], "dependent_actions": []}
                ],
            },
            {
                # Exercises a condition key referenced by an action but missing
                # from the service's condition-keys table.
                "privilege": "ImportCertificate",
                "description": "Import a certificate",
                "access_level": "Write",
                "resource_types": [
                    {
                        "resource_type": "certificate",
                        "condition_keys": ["aws:UnlistedKey"],
                        "dependent_actions": [],
                    }
                ],
            },
        ],
    }
]


def _build(tmp_path):
    session, engine = connect(str(tmp_path / "iam.db"))
    Base.metadata.create_all(engine)
    create_database(session, ACM_FIXTURE)
    return session


def _condition_keys(session, action_name):
    rows = session.execute(
        text(
            """
            SELECT c.name
            FROM action a
            JOIN action_condition ac ON ac.action_id = a.id
            JOIN condition c ON c.id = ac.condition_id
            WHERE a.name = :name
            ORDER BY c.name
            """
        ),
        {"name": action_name},
    ).fetchall()
    return [row[0] for row in rows]


def test_action_condition_table_exists(tmp_path):
    session = _build(tmp_path)
    exists = session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='action_condition'")
    ).fetchone()
    assert exists is not None


def test_resourceless_action_keeps_action_level_keys(tmp_path):
    # The regression this whole change is about: an action with no resource type
    # must still expose its condition keys.
    session = _build(tmp_path)
    assert _condition_keys(session, "acm:RequestCertificate") == [
        "acm:DomainNames",
        "acm:KeyAlgorithm",
        "acm:ValidationMethod",
        "aws:RequestTag/${TagKey}",
        "aws:TagKeys",
    ]


def test_resource_scoped_action_uses_actions_table_keys(tmp_path):
    # Keys come from the action's own row, not from every key the resource
    # supports (the certificate resource also supports aws:ResourceTag).
    session = _build(tmp_path)
    assert _condition_keys(session, "acm:AddTagsToCertificate") == [
        "aws:RequestTag/${TagKey}",
        "aws:TagKeys",
    ]


def test_action_without_condition_keys_has_none(tmp_path):
    session = _build(tmp_path)
    assert _condition_keys(session, "acm:DescribeCertificate") == []


def test_key_absent_from_conditions_table_is_still_linked(tmp_path):
    session = _build(tmp_path)
    assert _condition_keys(session, "acm:ImportCertificate") == ["aws:UnlistedKey"]


def test_normalize_condition_key():
    assert normalize_condition_key("aws:RequestTag/${TagKey}") == "aws:RequestTag/${TagKey}"
    assert normalize_condition_key("aws: TagKeys ") == "aws:TagKeys"
