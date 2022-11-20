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

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
            cls.connect: "c",
            cls.temporary: "T",
        }


class ForeignDataWrapperGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class ForeignServerGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class ForeignTableGrants(Grants):
    select = "SELECT"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "s",
        }


class FunctionGrants(Grants):
    execute = "EXECUTE"
    all = "ALL"

    def default(self):
        return [self.execute]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.execute: "X",
        }


class LanguageGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class LargeObjectGrants(Grants):
    select = "SELECT"
    update = "UPDATE"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "r",
            cls.update: "w",
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

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "r",
            cls.update: "w",
            cls.insert: "a",
            cls.references: "x",
            cls.delete: "d",
            cls.trigger: "t",
            cls.truncate: "D",
        }


class TablespaceGrants(Grants):
    create = "CREATE"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
        }


class TypeGrants(Grants):
    usage = "USAGE"
    all = "ALL"

    def default(self):
        return [self.usage]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class SchemaGrants(Grants):
    create = "CREATE"
    usage = "USAGE"
    all = "ALL"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
            cls.usage: "C",
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

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "r",
            cls.update: "w",
            cls.usage: "a",
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
    function = "FUNCTION"
    table = "TABLE"
    type = "TYPE"
    sequence = "SEQUENCE"

    def to_variants(self):
        return {
            self.table: TableGrants,
            self.sequence: SequenceGrants,
            self.function: FunctionGrants,
            self.type: TypeGrants,
        }[self]
