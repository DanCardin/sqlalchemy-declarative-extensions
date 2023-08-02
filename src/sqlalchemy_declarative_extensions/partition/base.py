import enum
from dataclasses import dataclass
from typing import Any, TypeVar

from sqlalchemy import Column, Table, types
from sqlalchemy.engine import Connectable
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@enum.unique
class ParitionBy(enum.Enum):
    range = "RANGE"
    list = "LIST"
    hash = "HASH"


@dataclass
class Partition:
    by: ParitionBy
    columns: list[str]

    @classmethod
    def by_range(cls, column, *columns: str, sub_partition=True):
        return cls(by=ParitionBy.range, columns=[column, *columns])

    def __call__(self, cls):
        columns = ", ".join(self.columns)
        cls.__table_args__ = {"postgresql_partition_by": f"{self.by.value} ({columns})"}
        cls.__partition__ = self

        return cls

    def create(self, *values):
        pass


T = TypeVar("T")


def generate_model(model: type[T], **values) -> type[T]:
    return type(model.__name__, (model,), {})


@Partition.by_range("id")
class Foo(Base):
    id = Column(types.Integer(), primary_key=True)


def generate_name(table: Table, column_name: str, value: Any) -> str:
    column = getattr(table.c, column_name)

    # Clean up invalid characters for table names
    part = column.compile(value)
    part = part.replace("'", "").replace("-", "").replace(" ", "_")
    return f"{table.fullname}_{part}"


def create_partition_queries(
    session: Connectable, table: Table, parent_name: str, columns: list[tuple[str, Any]]
):
    column, *remaining_columns = columns
    create_table_queries = []
    partition_name = generate_name(table, column[0], column[1])

    sub_partition_partition = ""
    if len(partition_specs) > 1:
        create_table_queries, sub_partition_partition = create_partition_queries(
            session,
            base_table,
            partition_name,
            partition_specs[1:],
        )

    value_str = ""
    partition_partition_sql = ""
    if isinstance(base_partition.value, datetime.date):
        value_str = f"""
            FOR VALUES FROM ('{base_partition.value}')
            TO ('{base_partition.value + datetime.timedelta(days=1)}')
        """
        partition_partition_sql = f"PARTITION BY RANGE({base_partition.column})"
    else:
        value_str = f"FOR VALUES IN ({base_partition.value})"
        partition_partition_sql = f"PARTITION BY LIST({base_partition.column})"

    create_table = f"""
        CREATE TABLE {partition_name} PARTITION OF {parent_name}
        {value_str}
        {sub_partition_partition};
    """
    create_table_queries.insert(0, (create_table, parent_name, partition_name))

    return create_table_queries, partition_partition_sql
