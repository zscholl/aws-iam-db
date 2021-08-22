import json
from typing import Tuple

from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.schema import ForeignKey, Table

import typer


Base = declarative_base()  # pylint: disable=invalid-name

action_resource_table = Table(
    "action_resource",
    Base.metadata,
    Column("action_id", Integer, ForeignKey("action.id")),
    Column("resource_id", Integer, ForeignKey("resource.id")),
)

resource_condition_table = Table(
    "resource_condition",
    Base.metadata,
    Column("resource_id", Integer, ForeignKey("resource.id")),
    Column("condition_id", Integer, ForeignKey("condition.id")),
)


class DependentAction(Base):
    """SQLAlchemy Declarative configuration for the Dependent Actions table"""

    __tablename__ = "dependent_action"

    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey("action.id"))
    name = Column(String())
    resource = Column(String())

    def __repr__(self):
        return "<DependentAction(name='%s', resource='%s')>" % (
            self.name,
            self.resource,
        )


class Action(Base):
    """SQLAlchemy Declarative configuration for the IAM Actions table"""

    __tablename__ = "action"
    id = Column(Integer, primary_key=True)
    name = Column(String(), index=True)
    description = Column(String())
    access_level = Column(String(), index=True)
    resources = relationship("Resource", secondary=action_resource_table)
    dependent_actions = relationship("DependentAction")

    def __repr__(self):
        return "<Action(name='%s', description='%s', access_level='%s')>" % (
            self.name,
            self.description,
            self.access_level,
        )


class Resource(Base):
    """SQLAlchemy Declarative configuration for the Resource Types table"""

    __tablename__ = "resource"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    arn = Column(String())
    required = Column(Boolean())
    condition_keys = relationship(
        "Condition", secondary=resource_condition_table, back_populates="resources"
    )

    def __repr__(self):
        return "<Arn(arn='%s', name='%s')>" % (self.arn, self.name)


class Condition(Base):
    """SQLAlchemy Declarative configuration for the Condition Keys table"""

    __tablename__ = "condition"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    description = Column(String())
    type = Column(String())
    resources = relationship(
        "Resource", secondary=resource_condition_table, back_populates="condition_keys"
    )

    def __repr__(self):
        return "<Condition(name='%s', type='%s', description='%s')>" % (
            self.name,
            self.type,
            self.description,
        )


def create_database(db_session: Session, json_data: list):
    with typer.progressbar(json_data, label="Creating database") as progress:
        for row in progress:
            # 'conditions', 'prefix', 'privileges', 'resources', 'service_name'
            for cond in row["conditions"]:
                new_cond = Condition(
                    name=cond["condition"],
                    description=cond["description"],
                    type=cond["type"],
                )
                db_session.add(new_cond)
            for res in row["resources"]:
                new_res = Resource(
                    name=res["resource"],
                    arn=res["arn"].rstrip("*"),
                    required=res["arn"].endswith("*"),
                )
                if len(res["condition_keys"]) > 0:
                    conditions = (
                        db_session.query(Condition)
                        .filter(Condition.name.in_(res["condition_keys"]))
                        .all()
                    )
                    new_res.condition_keys.extend(conditions)
                db_session.add(new_res)
            for priv in row["privileges"]:
                # pull resources
                resource_names = [
                    res["resource_type"].rstrip("*") for res in priv["resource_types"]
                ]
                resources = (
                    db_session.query(Resource)
                    .filter(Resource.name.in_(resource_names))
                    .all()
                )
                # create dependent actions
                dep_actions = []
                for res_type in priv["resource_types"]:
                    dep_actions.extend(
                        [
                            DependentAction(
                                name=act, resource=res_type["resource_type"].rstrip("*")
                            )
                            for act in res_type["dependent_actions"]
                        ]
                    )
                new_priv = Action(
                    name=f"{row['prefix']}:{priv['privilege']}",
                    description=priv["description"],
                    access_level=priv["access_level"],
                    resources=resources,
                    dependent_actions=dep_actions,
                )
                db_session.add(new_priv)
    db_session.commit()
    typer.echo("Database created!")


def connect(db_path: str) -> Tuple[Session, Engine]:
    engine = create_engine(f"sqlite:///{db_path}")
    return Session(engine), engine


def init(iam_data_file: str, db_path: str):
    with open(iam_data_file, "r") as data_file:
        iam_data = json.load(data_file)
    session, engine = connect(db_path)
    Base.metadata.create_all(engine)
    create_database(session, iam_data)
