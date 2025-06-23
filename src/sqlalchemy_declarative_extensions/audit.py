from __future__ import annotations

from typing import Callable, TypeVar, cast

from sqlalchemy import Column, MetaData, Table, text, types

from sqlalchemy_declarative_extensions import (
    Function,
    register_function,
    register_trigger,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.trigger import Trigger
from sqlalchemy_declarative_extensions.sql import quote_name

default_primary_key = Column(
    "audit_pk", types.Integer(), primary_key=True, autoincrement=True
)


T = TypeVar("T")
AUDIT_PK = "audit_pk"
AUDIT_OPERATION = "audit_operation"
AUDIT_TIMESTAMP = "audit_timestamp"
AUDIT_CURRENT_USER = "audit_current_user"


def audit(
    *,
    primary_key: Column = default_primary_key,
    schema: str | None = None,
    ignore_columns: set = set(),
    context_columns: list[Column] | None = None,
    insert: bool = True,
    update: bool = True,
    delete: bool = True,
) -> Callable[[T], T]:
    def decorator(model: T) -> T:
        return audit_model(
            model,
            primary_key=primary_key,
            schema=schema,
            ignore_columns=ignore_columns,
            context_columns=context_columns,
            insert=insert,
            update=update,
            delete=delete,
        )

    return decorator


def audit_model(
    model: T,
    primary_key: Column = default_primary_key,
    schema: str | None = None,
    ignore_columns: set = set(),
    context_columns: list[Column] | None = None,
    insert: bool = True,
    update: bool = True,
    delete: bool = True,
) -> T:
    table = getattr(model, "__table__", None)
    if table is None:  # pragma: no cover
        raise ValueError(f"{model} is not a valid model, lacks __table__ attribute.")

    table = audit_table(
        table,
        primary_key=primary_key,
        schema=schema,
        ignore_columns=ignore_columns,
        context_columns=context_columns,
        insert=insert,
        update=update,
        delete=delete,
    )
    model.__audit_table__ = table  # type: ignore
    return model


def audit_table(
    table: Table,
    primary_key: Column = default_primary_key,
    schema: str | None = None,
    ignore_columns: set = set(),
    context_columns: list[Column] | None = None,
    insert: bool = True,
    update: bool = True,
    delete: bool = True,
):
    metadata = getattr(table, "metadata", None)
    assert metadata

    audit_table = create_audit_table(
        metadata,
        table,
        primary_key=primary_key,
        schema=schema,
        ignore_columns=ignore_columns,
        context_columns=context_columns,
    )
    create_audit_functions(
        metadata,
        table,
        audit_table,
        insert=insert,
        update=update,
        delete=delete,
    )
    create_audit_triggers(
        table.metadata,
        table,
        insert=insert,
        update=update,
        delete=delete,
    )
    return audit_table


def create_audit_table(
    metadata: MetaData,
    table: Table,
    primary_key: Column = default_primary_key,
    schema: str | None = None,
    ignore_columns: set = set(),
    context_columns: list[Column] | None = None,
) -> Table:
    naming_convention = cast(
        str, metadata.naming_convention.get("audit_function", "%(table_name)s_audit")
    )
    table_name = naming_convention % {
        "table_fullname": table.fullname,
        "schema": schema or table.schema,
        "table_name": table.name,
    }

    primary_key_column = Column(
        "audit_pk", primary_key.type, nullable=primary_key.nullable, primary_key=True
    )

    concrete_context_columns = []
    for column in context_columns or []:
        concrete_context_columns.append(
            Column(
                f"audit_{column.name}",
                column.type,
                nullable=column.nullable,
                info={"context_column": True},
            )
        )

    table_columns = [
        Column(col.name, col.type, nullable=True)
        for col in table.columns.values()
        if col.name not in ignore_columns
    ]

    return Table(
        table_name,
        metadata,
        primary_key_column,
        Column(AUDIT_OPERATION, types.Unicode(1), nullable=False),
        Column(AUDIT_TIMESTAMP, types.DateTime(timezone=True), nullable=False),
        Column(AUDIT_CURRENT_USER, types.Unicode(64), nullable=False),
        *concrete_context_columns,
        *table_columns,
        schema=schema or table.schema,
    )


def create_audit_functions(
    metadata: MetaData,
    table: Table,
    audit_table: Table,
    insert: bool = True,
    update: bool = True,
    delete: bool = True,
) -> list[Function]:
    naming_convention = cast(
        str,
        metadata.naming_convention.get(
            "audit_function", "%(schema)s_%(table_name)s_audit"
        ),
    )
    function_name = naming_convention % {
        "schema": table.schema or "public",
        "table_name": table.name,
    }

    audit_columns = []
    old_elements = []
    new_elements = []
    for column in audit_table.columns:
        if column.name == AUDIT_PK:
            continue

        audit_columns.append(quote_name(column.name))

        if column.name in {
            AUDIT_PK,
            AUDIT_OPERATION,
            AUDIT_TIMESTAMP,
            AUDIT_CURRENT_USER,
        }:
            continue

        if column.info.get("context_column"):
            setting_name = column.name.replace("_", ".", 1)
            missing_ok = str(column.nullable).lower()
            type_name = column.type.compile()
            value = f"current_setting('{setting_name}', {missing_ok})::{type_name}"

            old_elements.append(value)
            new_elements.append(value)
        else:
            old_elements.append(f'OLD."{column.name}"')
            new_elements.append(f'NEW."{column.name}"')

    audit_columns_str = ", ".join(audit_columns)
    old_elements_str = ", ".join(old_elements)
    new_elements_str = ", ".join(new_elements)

    ops = [
        (insert, "INSERT", new_elements_str),
        (update, "UPDATE", new_elements_str),
        (delete, "DELETE", old_elements_str),
    ]

    functions = []
    for enabled, op, elements in ops:
        if not enabled:
            continue

        op_key = op[0]
        function = Function(
            "_".join([function_name, op.lower()]),
            f"""
            BEGIN
            INSERT INTO {quote_name(audit_table.fullname)} ({audit_columns_str})
            SELECT '{op_key}', now(), current_user, {elements};
            RETURN NULL;
            END
            """,
            returns="TRIGGER",
            language="plpgsql",
        )
        functions.append(function)
        register_function(metadata, function)

    return functions


def create_audit_triggers(
    metadata: MetaData,
    table: Table,
    insert: bool = True,
    update: bool = True,
    delete: bool = True,
) -> list[Trigger]:
    naming_convention = cast(
        str,
        metadata.naming_convention.get(
            "audit_trigger", "%(schema)s_%(table_name)s_audit"
        ),
    )
    function_name = naming_convention % {
        "schema": table.schema or "public",
        "table_name": table.name,
    }
    trigger_name = naming_convention % {
        "schema": table.schema or "public",
        "table_name": table.name,
    }

    ops = [
        (insert, "insert"),
        (update, "update"),
        (delete, "delete"),
    ]

    triggers = []
    for enabled, op in ops:
        if not enabled:
            continue

        trigger = Trigger.after(
            op,
            on=table.fullname,
            execute="_".join([function_name, op]),
            name="_".join([trigger_name, op]),
        ).for_each_row()
        triggers.append(trigger)
        register_trigger(metadata, trigger)

    return triggers


def set_context_values(connectable, **values):
    """Set transaction-local context values, to be included on audit-tables."""
    for name, value in values.items():
        if value is None:
            continue

        statement = f"SET LOCAL audit.{name} = '{value}'"
        connectable.execute(text(statement))


__all__ = [
    "audit",
    "audit_model",
    "audit_table",
    "create_audit_functions",
    "create_audit_table",
    "create_audit_triggers",
    "set_context_values",
]
