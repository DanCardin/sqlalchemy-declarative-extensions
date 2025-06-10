from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Sequence, Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import get_procedure_cls, get_procedures
from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.procedure.base import Procedure, Procedures


@dataclass
class CreateProcedureOp(ExecuteOp):
    procedure: Procedure

    def reverse(self):
        return DropProcedureOp(self.procedure)

    def to_sql(self) -> list[str]:
        return self.procedure.to_sql_create()


@dataclass
class UpdateProcedureOp(ExecuteOp):
    from_procedure: Procedure
    procedure: Procedure

    def reverse(self):
        return UpdateProcedureOp(self.procedure, self.from_procedure)

    def to_sql(self) -> list[str]:
        return self.procedure.to_sql_update()


@dataclass
class DropProcedureOp(ExecuteOp):
    procedure: Procedure

    def reverse(self):
        return CreateProcedureOp(self.procedure)

    def to_sql(self) -> list[str]:
        return self.procedure.to_sql_drop()


Operation = Union[CreateProcedureOp, UpdateProcedureOp, DropProcedureOp]


def compare_procedures(
    connection: Connection, procedures: Procedures
) -> list[Operation]:
    result: list[Operation] = []

    procedures_by_name = {f.qualified_name: f for f in procedures.procedures}
    expected_procedure_names = set(procedures_by_name)

    existing_procedures = filter_procedures(
        get_procedures(connection), procedures.ignore
    )
    existing_procedures_by_name = {r.qualified_name: r for r in existing_procedures}
    existing_procedure_names = set(existing_procedures_by_name)

    new_procedure_names = expected_procedure_names - existing_procedure_names
    removed_procedure_names = existing_procedure_names - expected_procedure_names

    procedure_cls = get_procedure_cls(connection)
    for procedure in procedures:
        procedure_name = procedure.qualified_name

        procedure_created = procedure_name in new_procedure_names

        concrete_procedure = procedure_cls.from_unknown_procedure(procedure)
        normalized_procedure = concrete_procedure.normalize()

        if procedure_created:
            result.append(CreateProcedureOp(normalized_procedure))
        else:
            existing_procedure = existing_procedures_by_name[procedure_name]

            normalized_existing_procedure = existing_procedure.normalize()

            if normalized_existing_procedure != normalized_procedure:
                result.append(
                    UpdateProcedureOp(
                        normalized_existing_procedure, normalized_procedure
                    )
                )

    if not procedures.ignore_unspecified:
        for removed_procedure in removed_procedure_names:
            procedure = existing_procedures_by_name[removed_procedure]
            result.append(DropProcedureOp(procedure))

    return result


def filter_procedures(
    procedures: Sequence[Procedure], exclude: list[str]
) -> list[Procedure]:
    return [
        f
        for f in procedures
        if not any(
            fnmatch.fnmatch(f.qualified_name, exclusion) for exclusion in exclude
        )
    ]
