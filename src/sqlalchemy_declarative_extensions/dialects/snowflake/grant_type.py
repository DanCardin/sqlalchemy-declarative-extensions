from typing import List, TypeVar

from typing_extensions import Self

from sqlalchemy_declarative_extensions.dialects.from_string import FromStrings


class GrantOptions(FromStrings):
    def default(self: Self) -> List[Self]:
        """Return the default grants given by the database for the current grant kind.

        There are some default privileges on some types of objects to PUBLIC.
        No privileges are granted to PUBLIC by default on tables, columns,
        schemas or tablespaces.
        """
        return []

    @classmethod
    def all(cls: type[Self]) -> list[Self]:
        return list(cls)


class DatabaseGrants(GrantOptions):
    create = "CREATE"
    modify = "MODIFY"
    monitor = "MONITOR"
    usage = "USAGE"


class FileFormatGrants(GrantOptions):
    usage = "USAGE"


class FunctionGrants(GrantOptions):
    usage = "USAGE"


class ProcedureGrants(GrantOptions):
    usage = "USAGE"


class TableGrants(GrantOptions):
    select = "SELECT"
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"
    references = "REFERENCES"
    apply_budget = "APPLYBUDGET"
    evolve_schema = "EVOLVE SCHEMA"


class TaskGrants(GrantOptions):
    monitor = "MONITOR"


class TypeGrants(GrantOptions):
    usage = "USAGE"


class SchemaGrants(GrantOptions):
    create = "CREATE"
    usage = "USAGE"
    modify = "MODIFY"
    monitor = "MONITOR"


class StageGrants(GrantOptions):
    usage = "USAGE"
    read = "READ"


class StreamGrants(GrantOptions):
    select = "SELECT"


class SequenceGrants(GrantOptions):
    usage = "USAGE"


class ViewGrants(GrantOptions):
    references = "REFERENCES"
    select = "SELECT"


class WarehouseGrants(GrantOptions):
    apply_budget = "APPLYBUDGET"
    modify = "MODIFY"
    monitor = "MONITOR"
    operate = "OPERATE"
    usage = "USAGE"


G = TypeVar(
    "G",
    DatabaseGrants,
    FunctionGrants,
    SchemaGrants,
    SequenceGrants,
    TableGrants,
    TaskGrants,
    TypeGrants,
    WarehouseGrants,
)


class GrantTypes(FromStrings):
    file_format = "FILE FORMAT"
    database = "DATABASE"
    function = "FUNCTION"
    procedure = "PROCEDURE"
    schema = "SCHEMA"
    sequence = "SEQUENCE"
    stage = "STAGE"
    stream = "STREAM"
    table = "TABLE"
    task = "TASK"
    type = "TYPE"
    warehouse = "WAREHOUSE"
    view = "VIEW"

    def to_variants(self):
        return {
            self.database: DatabaseGrants,
            self.file_format: FileFormatGrants,
            self.function: FunctionGrants,
            self.procedure: ProcedureGrants,
            self.schema: SchemaGrants,
            self.sequence: SequenceGrants,
            self.stage: StageGrants,
            self.stream: StreamGrants,
            self.table: TableGrants,
            self.task: TaskGrants,
            self.type: TypeGrants,
            self.view: ViewGrants,
            self.warehouse: WarehouseGrants,
        }[self]


class DefaultGrantTypes(FromStrings):
    file_format = "FILE FORMAT"
    function = "FUNCTION"
    procedure = "PROCEDURE"
    schema = "SCHEMA"
    sequence = "SEQUENCE"
    stage = "STAGE"
    stream = "STREAM"
    table = "TABLE"
    task = "TASK"
    type = "TYPE"
    view = "VIEW"

    # views stages file_formats, streams
    #
    # @classmethod
    # def from_relkind(cls, relkind: str):
    #     return cls._str_to_kind()[relkind]

    def to_variants(self):
        return self.to_grant_type().to_variants()

    def to_grant_type(self):
        return {
            self.function: GrantTypes.function,
            self.procedure: GrantTypes.procedure,
            self.schema: GrantTypes.schema,
            self.sequence: GrantTypes.sequence,
            self.table: GrantTypes.table,
            self.task: GrantTypes.task,
            self.type: GrantTypes.type,
            self.view: GrantTypes.view,
            self.file_format: GrantTypes.file_format,
            self.stream: GrantTypes.stream,
            self.stage: GrantTypes.stage,
        }[self]
