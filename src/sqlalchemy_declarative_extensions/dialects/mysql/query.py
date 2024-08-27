from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.mysql.function import (
    Function,
    FunctionDataAccess,
    FunctionSecurity,
)
from sqlalchemy_declarative_extensions.dialects.mysql.procedure import (
    Procedure,
    ProcedureSecurity,
)
from sqlalchemy_declarative_extensions.dialects.mysql.schema import (
    functions_query,
    procedures_query,
    schema_exists_query,
    triggers_query,
    views_query,
)
from sqlalchemy_declarative_extensions.dialects.mysql.trigger import (
    Trigger,
    TriggerEvents,
    TriggerTimes,
)
from sqlalchemy_declarative_extensions.function import Function as BaseFunction
from sqlalchemy_declarative_extensions.procedure import Procedure as BaseProcedure
from sqlalchemy_declarative_extensions.view.base import View


def get_views_mysql(connection: Connection):
    current_database = connection.engine.url.database
    return [
        View(
            v.name,
            v.definition,
            schema=v.schema if v.schema != current_database else None,
        )
        for v in connection.execute(views_query).fetchall()
    ]


def get_triggers_mysql(connection: Connection) -> list[Trigger]:
    assert connection.engine.url.database
    database: str = connection.engine.url.database

    triggers = []
    for t in connection.execute(triggers_query, {"schema": database}).fetchall():
        triggers.append(
            Trigger(
                name=t.name,
                time=TriggerTimes(t.time),
                event=TriggerEvents(t.event),
                on=t.on_name,
                execute=t.statement,
            )
        )
    return triggers


def check_schema_exists_mysql(connection: Connection, name: str) -> bool:
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return not bool(row)


def get_procedures_mysql(connection: Connection) -> Sequence[BaseProcedure]:
    assert connection.engine.url.database
    database: str = connection.engine.url.database

    procedures = []
    for p in connection.execute(procedures_query, {"schema": database}).fetchall():
        procedures.append(
            Procedure(
                name=p.name,
                definition=p.definition,
                security=(
                    ProcedureSecurity.definer
                    if p.security == "DEFINER"
                    else ProcedureSecurity.invoker
                ),
            )
        )
    return procedures


def get_functions_mysql(connection: Connection) -> Sequence[BaseFunction]:
    assert connection.engine.url.database
    database: str = connection.engine.url.database

    functions = []
    for f in connection.execute(functions_query, {"schema": database}).fetchall():
        functions.append(
            Function(
                name=f.name,
                definition=f.definition,
                security=(
                    FunctionSecurity.definer
                    if f.security == "DEFINER"
                    else FunctionSecurity.invoker
                ),
                returns=f.return_type,
                deterministic=f.deterministic == "YES",
                data_access=FunctionDataAccess(f.data_access),
            )
        )
    return functions
