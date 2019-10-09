from typing import List

from sqlalchemy_declarative_extensions.grant.postgresql.base import (
    DefaultGrantStatement,
    Grant,
)
from sqlalchemy_declarative_extensions.grant.postgresql.grant_type import GrantTypes


def parse_acl(acl: str, object_type: str) -> List[DefaultGrantStatement]:
    """Parse postgres' acl mini language.

    Port of ``parseAclItem`` from `dumputils.c`.

    Arguments:
        acl: ACL, e.g. ``['alice=arwdDxt/alice', 'bob=arwdDxt/alice']``
        object_type: the kind of object being parsed.
    """
    type = _object_type_symbol_map[object_type]
    variants = type.to_variants()

    result = []
    grants: List[Grant] = []
    grants_with_grant_option: List[Grant] = []

    eq_pos, grantee = get_acl_username(acl)
    assert acl[eq_pos] == "="

    if not grantee:
        grantee = "PUBLIC"

    slash_pos = acl.index("/", eq_pos)
    _, grantor = get_acl_username(acl[slash_pos + 1 :])

    priv = acl[eq_pos + 1 : slash_pos]

    for privilege, symbol in variants.acl_symbols.items():
        pos = priv.find(symbol)

        if pos >= 0:
            if len(priv) > pos + 1 and priv[pos + 1] == "*":
                grants_with_grant_option.append(privilege)
            else:
                grants.append(privilege)

    if grants:
        grant = DefaultGrantStatement(
            Grant(
                target_role=grantee,
                grantor=grantor,
                grants=tuple(grants),  # type: ignore
            )
        )
        result.append(grant)

    if grants_with_grant_option:
        grant = DefaultGrantStatement(
            Grant(
                grantee,
                grantor=grantor,
                grants=tuple(grants_with_grant_option),  # type: ignore
                grant_option=True,
            )
        )
        result.append(grant)

    return result


def get_acl_username(acl: str):
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
