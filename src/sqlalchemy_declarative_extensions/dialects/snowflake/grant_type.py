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


class DatabaseGrants(GrantOptions):
    create = "CREATE"
    modify = "MODIFY"
    monitor = "MONITOR"
    usage = "USAGE"


class FunctionGrants(GrantOptions):
    execute = "USAGE"


class TableGrants(GrantOptions):
    select = "SELECT"
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"
    references = "REFERENCES"
    apply_budget = "APPLYBUDGET"
    evolve_schema = "EVOLVE SCHEMA"


class TypeGrants(GrantOptions):
    usage = "USAGE"


class SchemaGrants(GrantOptions):
    create = "CREATE"
    usage = "USAGE"
    modify = "MODIFY"
    monitor = "MONITOR"


class SequenceGrants(GrantOptions):
    usage = "USAGE"


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
    TypeGrants,
    WarehouseGrants,
)


class GrantTypes(FromStrings):
    database = "DATABASE"
    function = "FUNCTION"
    schema = "SCHEMA"
    sequence = "SEQUENCE"
    table = "TABLE"
    type = "TYPE"
    warehouse = "WAREHOUSE"

    def to_variants(self):
        return {
            self.database: DatabaseGrants,
            self.function: FunctionGrants,
            self.schema: SchemaGrants,
            self.sequence: SequenceGrants,
            self.table: TableGrants,
            self.type: TypeGrants,
            self.warehouse: WarehouseGrants,
        }[self]


class FutureGrantTypes(FromStrings):
    function = "FUNCTION"
    table = "TABLE"
    type = "TYPE"
    sequence = "SEQUENCE"
    sequence = "SEQUENCE"

    # procedures tasks views stages file_formats, streams

    @classmethod
    def _str_to_kind(cls):
        return {
            "f": cls.function,
            "r": cls.table,
            "T": cls.type,
            "S": cls.sequence,
        }

    @classmethod
    def from_relkind(cls, relkind: str):
        return cls._str_to_kind()[relkind]

    def to_variants(self):
        return {
            self.table: TableGrants,
            self.sequence: SequenceGrants,
            self.function: FunctionGrants,
            self.type: TypeGrants,
        }[self]

    def to_grant_type(self):
        return {
            self.table: GrantTypes.table,
            self.sequence: GrantTypes.sequence,
            self.function: GrantTypes.function,
            self.type: GrantTypes.type,
        }[self]
