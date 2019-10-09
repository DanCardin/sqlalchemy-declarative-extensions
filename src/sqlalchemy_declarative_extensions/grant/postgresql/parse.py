from typing import Dict, Iterable, List, Sequence, Tuple

from sqlalchemy_declarative_extensions.grant.postgresql.base import (
    DefaultGrant,
    GrantPrivileges,
)
from sqlalchemy_declarative_extensions.grant.postgresql.grant_type import (
    DatabaseGrants,
    ForeignDataWrapperGrants,
    ForeignServerGrants,
    ForeignTableGrants,
    FunctionGrants,
    Grants,
    GrantTypes,
    LanguageGrants,
    LargeObjectGrants,
    SchemaGrants,
    SequenceGrants,
    TableGrants,
    TablespaceGrants,
    TypeGrants,
)


def parse_acl(acl: Sequence[str], object_type: str) -> List[GrantPrivileges]:
    """Parse postgres' acl mini language.

    Port of ``parseAclItem`` from `dumputils.c`_

    Arguments:
        acl: ACL, e.g. ``['alice=arwdDxt/alice', 'bob=arwdDxt/alice']``
        object_type: the kind of object being parsed.
    """
    type = _object_type_symbol_map[object_type]

    result = []

    eq_pos, grantee = get_acl_username(acl)
    assert acl[eq_pos] == "="

    if not grantee:
        grantee = "PUBLIC"

    slash_pos = acl.index("/", eq_pos)
    _, grantor = get_acl_username(acl[slash_pos + 1 :])

    priv = acl[eq_pos + 1 : slash_pos]

    grants: List[Grants] = []
    grants_with_grant_option: List[Grants] = []

    symbols = _grant_type_symbol_map[type]
    for symbol, privilege in symbols:
        pos = priv.find(symbol)
        if pos >= 0:
            if len(priv) > pos + 1 and priv[pos + 1] == "*":
                grants_with_grant_option.append(privilege)
            else:
                grants.append(privilege)

    if grants:
        grant = DefaultGrant(
            GrantPrivileges(
                target_role=grantee,
                grantor=grantor,
                grants=tuple(grants),  # type: ignore
            )
        )
        result.append(grant)

    if grants_with_grant_option:
        grant = DefaultGrant(
            GrantPrivileges(
                grantee,
                grantor=grantor,
                grants=tuple(grants_with_grant_option),  # type: ignore
                grant_option=True,
            )
        )
        result.append(grant)

    return result


def get_default_privileges(type: GrantTypes, owner: str) -> List[GrantPrivileges]:
    """Return the set of privileges granted to an object by default.

    This can be called when the ACL item from PostgreSQL is NULL to determine
    the implicit access privileges.

    .. seealso:: https://www.postgresql.org/docs/10/static/sql-grant.html
    """
    grants = type.to_variants()
    priv_list = [
        # "the owner has all privileges by default"
        # "PostgreSQL treats the owner's privileges as having been granted by the
        # owner to themselves"
        GrantPrivileges(target_role=owner, grantor=owner, grants=[grants.all]),
        GrantPrivileges(target_role="PUBLIC", grantor=owner, grants=grants.default()),
    ]

    return priv_list


def get_acl_username(acl):
    """Port ``copyAclUserName`` from ``dumputils.c``."""
    i = 0
    output = ""

    while i < len(acl) and acl[i] != "=":
        # If user name isn't quoted, then just add it to the output buffer
        if acl[i] != '"':
            output += acl[i]
            i += 1
        else:
            # Otherwise, it's a quoted username
            i += 1

            if i == len(acl):
                raise ValueError("ACL syntax error: unterminated quote.")

            # Loop until we come across an unescaped quote
            while not (acl[i] == '"' and acl[i + 1] != '"'):
                # Quoting convention is to escape " as "".
                if acl[i] == '"' and acl[i + 1] == '"':
                    i += 1

                output += acl[i]
                i += 1

                if i == len(acl):
                    raise ValueError("ACL syntax error: unterminated quote.")

            i += 1

    return i, output


_object_type_symbol_map = {
    "r": GrantTypes.table,
    "S": GrantTypes.sequence,
    "f": GrantTypes.function,
    "T": GrantTypes.type,
    "n": GrantTypes.schema,
}

_grant_type_symbol_map: Dict[GrantTypes, Iterable[Tuple[str, Grants]]] = {
    GrantTypes.table: (
        ("r", TableGrants.select),
        ("w", TableGrants.update),
        ("a", TableGrants.insert),
        ("x", TableGrants.references),
        ("d", TableGrants.delete),
        ("t", TableGrants.trigger),
        ("D", TableGrants.truncate),
    ),
    GrantTypes.sequence: (
        ("r", SequenceGrants.select),
        ("w", SequenceGrants.update),
        ("a", SequenceGrants.usage),
    ),
    GrantTypes.function: (("X", FunctionGrants.execute),),
    GrantTypes.language: (("U", LanguageGrants.usage),),
    GrantTypes.schema: (("C", SchemaGrants.create), ("C", SchemaGrants.usage)),
    GrantTypes.database: (
        ("C", DatabaseGrants.create),
        ("c", DatabaseGrants.connect),
        ("T", DatabaseGrants.temporary),
    ),
    GrantTypes.tablespace: (("C", TablespaceGrants.create),),
    GrantTypes.type: (("U", TypeGrants.usage),),
    GrantTypes.foreign_data_wrapper: (("U", ForeignDataWrapperGrants.usage),),
    GrantTypes.foreign_server: (("U", ForeignServerGrants.usage),),
    GrantTypes.foreign_table: (("s", ForeignTableGrants.select),),
    GrantTypes.large_object: (
        ("r", LargeObjectGrants.select),
        ("w", LargeObjectGrants.update),
    ),
}
