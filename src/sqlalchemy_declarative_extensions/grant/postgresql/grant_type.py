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

    @property
    def acl_symbols(self):
        return {
            DatabaseGrants.create: "C",
            DatabaseGrants.connect: "c",
            DatabaseGrants.temporary: "T",
        }


class ForeignDataWrapperGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            ForeignDataWrapperGrants.usage: "U",
        }


class ForeignServerGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            ForeignServerGrants.usage: "U",
        }


class ForeignTableGrants(Grants):
    select = "SELECT"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            ForeignTableGrants.select: "s",
        }


class FunctionGrants(Grants):
    execute = "EXECUTE"
    all = "ALL"

    def default(self):
        return [self.execute]

    @property
    def acl_symbols(self):
        return {
            self.execute: "X",
        }


class LanguageGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]

    @property
    def acl_symbols(self):
        return {
            LanguageGrants.usage: "U",
        }


class LargeObjectGrants(Grants):
    select = "SELECT"
    update = "UPDATE"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            LargeObjectGrants.select: "r",
            LargeObjectGrants.update: "w",
        }


class TableGrants(Grants):
    select = "SELECT"
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"
    references = "REFERENCES"
    trigger = "TRIGGER"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            self.select: "r",
            self.update: "w",
            self.insert: "a",
            self.references: "x",
            self.delete: "d",
            self.trigger: "t",
            self.truncate: "D",
        }


class TablespaceGrants(Grants):
    create = "CREATE"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            TablespaceGrants.create: "C",
        }


class TypeGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]

    @property
    def acl_symbols(self):
        return {
            TypeGrants.usage: "U",
        }


class SchemaGrants(Grants):
    create = "CREATE"
    usage = "USAGE"
    all = "ALL"

    @property
    def acl_symbols(self):
        return {
            self.create: "C",
            self.usage: "C",
        }


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

    @property
    def acl_symbols(self):
        return {
            self.select: "r",
            self.update: "w",
            self.usage: "a",
        }


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
