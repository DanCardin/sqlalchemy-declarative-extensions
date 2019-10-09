from typing import List, TypeVar

from sqlalchemy_declarative_extensions.sql import FromStrings, FromStringsSelf


class Grants(FromStrings):
    def default(self: FromStringsSelf) -> List[FromStringsSelf]:
        """Return the default grants given by postgres for the current grant kind.

        PostgreSQL grants default privileges on some types of objects to PUBLIC.
        No privileges are granted to PUBLIC by default on tables, columns,
        schemas or tablespaces.
        """

        return []


class DatabaseGrants(Grants):
    create = "CREATE"
    connect = "CONNECT"
    temporary = "TEMPORARY"
    all = "ALL"

    def default(self):
        return [self.connect, self.temporary]


class ForeignDataWrapperGrants(Grants):
    usage = "USAGE"
    all = "ALL"


class ForeignServerGrants(Grants):
    usage = "USAGE"
    all = "ALL"


class ForeignTableGrants(Grants):
    select = "SELECT"
    all = "ALL"


class FunctionGrants(Grants):
    execute = "EXECUTE"
    all = "ALL"

    def default(self):
        return [self.execute]


class LanguageGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]


class LargeObjectGrants(Grants):
    select = "SELECT"
    update = "UPDATE"
    all = "ALL"


class TableGrants(Grants):
    select = "SELECT"
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"
    references = "REFERENCES"
    trigger = "TRIGGER"
    all = "ALL"


class TablespaceGrants(Grants):
    create = "CREATE"
    all = "ALL"


class TypeGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]


class SchemaGrants(Grants):
    create = "CREATE"
    usage = "USAGE"
    all = "ALL"


G = TypeVar(
    "G",
    DatabaseGrants,
    ForeignDataWrapperGrants,
    ForeignServerGrants,
    ForeignTableGrants,
    FunctionGrants,
    LanguageGrants,
    LargeObjectGrants,
    SchemaGrants,
    TableGrants,
    TablespaceGrants,
    TypeGrants,
)


class SequenceGrants(Grants):
    usage = "USAGE"
    select = "SELECT"
    update = "UPDATE"


class GrantTypes(FromStrings):
    database = "DATABASE"
    foreign_data_wrapper = "FOREIGN DATA WRAPPER"
    foreign_server = "FOREIGN SERVER"
    foreign_table = "FOREIGN TABLE"
    function = "FUNCTION"
    language = "LANGUAGE"
    large_object = "LARGE OBJECT"
    schema = "SCHEMA"
    sequence = "SEQUENCE"
    table = "TABLE"
    tablespace = "TABLESPACE"
    type = "TYPE"

    def to_variants(self):
        return {
            self.database: DatabaseGrants,
            self.function: FunctionGrants,
            self.language: LanguageGrants,
            self.schema: SchemaGrants,
            self.sequence: SequenceGrants,
            self.table: TableGrants,
            self.type: TypeGrants,
        }[self]


class DefaultGrantTypes(FromStrings):
    sequence = "SEQUENCE"
    table = "TABLE"
    function = "FUNCTION"
    type = "TYPE"

    def to_variants(self):
        return {
            self.table: TableGrants,
            self.sequence: SequenceGrants,
            self.function: FunctionGrants,
            self.type: TypeGrants,
        }[self]
