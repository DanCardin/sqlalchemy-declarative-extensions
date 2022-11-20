from typing import List

from sqlalchemy_declarative_extensions.grant.postgresql.base import (
    DefaultGrantStatement,
    PGGrant,
)
from sqlalchemy_declarative_extensions.grant.postgresql.grant_type import (
    DefaultGrantTypes,
    GrantTypes,
)


def parse_acl(
    acl: str, object_type: str, schema_name: str = "public"
) -> List[DefaultGrantStatement]:
    """Parse postgres' acl mini language.

    Port of ``parseAclItem`` from `dumputils.c`.

    Arguments:
        acl: ACL, e.g. ``['alice=arwdDxt/alice', 'bob=arwdDxt/alice']``
        object_type: the kind of object being parsed.
        schema_name: the name of the schema for which the ACL is defined
    """
    type = _object_type_symbol_map[object_type]
    variants = type.to_variants()

    grants_no_grant_option: List[PGGrant] = []
    grants_with_grant_option: List[PGGrant] = []

    eq_pos, grantee = get_acl_username(acl)
    assert acl[eq_pos] == "="

    if not grantee:
        grantee = "PUBLIC"

    slash_pos = acl.index("/", eq_pos)
    _, grantor = get_acl_username(acl[slash_pos + 1 :])

    priv = acl[eq_pos + 1 : slash_pos]

    for privilege, symbol in variants.acl_symbols().items():
        pos = priv.find(symbol)

        if pos >= 0:
            if len(priv) > pos + 1 and priv[pos + 1] == "*":
                grants_with_grant_option.append(privilege)
            else:
                grants_no_grant_option.append(privilege)

    grants = []
    if grants_no_grant_option:
        grant = PGGrant(
            target_role=grantee,
            grants=tuple(grants_no_grant_option),  # type: ignore
        )
        grants.append(grant)

    if grants_with_grant_option:
        grant = PGGrant(
            target_role=grantee,
            grants=tuple(grants_with_grant_option),  # type: ignore
            grant_option=True,
        )
        grants.append(grant)

    return [
        DefaultGrantStatement(
            privileges=grant,
            grant_type=type,
            in_schemas=(schema_name,),
            for_role=grantor,
        )
        for grant in grants
    ]


def get_acl_username(acl: str):
    """Port ``copyAclUserName`` from ``dumputils.c``."""
    i = 0
    output = ""

    acl_len = len(acl)
    while i < acl_len and acl[i] != "=":
        # If user name isn't quoted, then just add it to the output buffer
        if acl[i] != '"':
            output += acl[i]
            i += 1
        else:
            i += 1

            # Loop until we come across an unescaped quote
            while True:
                if i >= acl_len:
                    raise ValueError("ACL syntax error: unterminated quote.")

                char = acl[i]

                if char == '"':
                    # Quoting convention is to escape " as "".
                    has_next_char = i + 1 < acl_len
                    if not has_next_char:
                        break

                    next_char = acl[i + 1]
                    i += 1
                    if next_char != '"':
                        break

                output += char
                i += 1

    return i, output


_object_type_symbol_map = {
    "f": DefaultGrantTypes.function,
    "r": DefaultGrantTypes.table,
    "T": DefaultGrantTypes.type,
    "S": DefaultGrantTypes.sequence,
}

_grant_object_type_symbol_map = {
    "f": GrantTypes.function,
    "r": GrantTypes.table,
    "T": GrantTypes.type,
    "n": GrantTypes.schema,
    "S": GrantTypes.sequence,
}
