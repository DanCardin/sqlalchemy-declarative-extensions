from typing import List, TypeVar

from sqlalchemy_declarative_extensions.dialects.from_string import (
    FromStrings,
    FromStringsSelf,
)


class GrantOptions(FromStrings):
    def default(self: FromStringsSelf) -> List[FromStringsSelf]:
        """Return the default grants given by postgres for the current grant kind.

        PostgreSQL grants default privileges on some types of objects to PUBLIC.
        No privileges are granted to PUBLIC by default on tables, columns,
        schemas or tablespaces.
        """
        return []


class DatabaseGrants(GrantOptions):
    create = "CREATE"
    connect = "CONNECT"
    temporary = "TEMPORARY"

    def default(self):
        return [self.connect, self.temporary]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
            cls.connect: "c",
            cls.temporary: "T",
        }


class ForeignDataWrapperGrants(GrantOptions):
    usage = "USAGE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class ForeignServerGrants(GrantOptions):
    usage = "USAGE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class ForeignTableGrants(GrantOptions):
    select = "SELECT"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "s",
        }


class FunctionGrants(GrantOptions):
    execute = "EXECUTE"

    def default(self):
        return [self.execute]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.execute: "X",
        }


class LanguageGrants(GrantOptions):
    usage = "USAGE"

    def default(self):
        return [self.usage]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class LargeObjectGrants(GrantOptions):
    select = "SELECT"
    update = "UPDATE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "r",
            cls.update: "w",
        }


class TableGrants(GrantOptions):
    select = "SELECT"
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"
    references = "REFERENCES"
    trigger = "TRIGGER"

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


class TablespaceGrants(GrantOptions):
    create = "CREATE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
        }


class TypeGrants(GrantOptions):
    usage = "USAGE"

    def default(self):
        return [self.usage]

    @classmethod
    def acl_symbols(cls):
        return {
            cls.usage: "U",
        }


class SchemaGrants(GrantOptions):
    create = "CREATE"
    usage = "USAGE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.create: "C",
            cls.usage: "U",
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


class SequenceGrants(GrantOptions):
    usage = "USAGE"
    select = "SELECT"
    update = "UPDATE"

    @classmethod
    def acl_symbols(cls):
        return {
            cls.select: "r",
            cls.update: "w",
            cls.usage: "U",
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

    @classmethod
    def _str_to_kind(cls):
        return {
            "f": cls.function,
            "n": cls.schema,
            "S": cls.sequence,
            "r": cls.table,
            "T": cls.type,
            "v": cls.table,
        }

    @classmethod
    def from_relkind(cls, relkind: str):
        return cls._str_to_kind()[relkind]

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
