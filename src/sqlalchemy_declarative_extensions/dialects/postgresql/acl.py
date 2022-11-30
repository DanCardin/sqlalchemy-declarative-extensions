from typing import List, Optional, Tuple, TypeVar

from sqlalchemy_declarative_extensions.dialects.postgresql import (
    DefaultGrant,
    DefaultGrantStatement,
    DefaultGrantTypes,
    Grant,
    GrantStatement,
    GrantTypes,
)

GT = TypeVar("GT", DefaultGrantTypes, GrantTypes)


def parse_acl(
    acl: Optional[str],
    object_type: str,
    object_name: str,
    owner: Optional[str] = None,
    expanded: bool = False,
) -> List[GrantStatement]:
    type = GrantTypes.from_relkind(object_type)
    _, grants = _parse_acl(acl, type, owner=owner, expanded=expanded)

    return [
        GrantStatement(
            grant=grant,
            grant_type=type,
            targets=(object_name,),
        )
        for grant in grants
    ]


def parse_default_acl(
    acl: Optional[str],
    object_type: str,
    schema_name: str = "public",
    expanded: bool = False,
    current_role: Optional[str] = None,
) -> List[DefaultGrantStatement]:
    type = DefaultGrantTypes.from_relkind(object_type)

    grantor: Optional[str]
    grantor, grants = _parse_acl(acl, type, expanded=expanded)

    if current_role == grantor:
        grantor = None

    return [
        DefaultGrantStatement(
            grant=grant,
            default_grant=DefaultGrant(
                grant_type=type,
                in_schemas=(schema_name,),
                target_role=grantor,
            ),
        )
        for grant in grants
    ]


def _parse_acl(
    acl: Optional[str],
    type: GT,
    *,
    owner: Optional[str] = None,
    expanded: bool = False,
) -> Tuple[str, List[Grant]]:
    """Parse postgres' acl mini language.

    Port of ``parseAclItem`` from `dumputils.c`.
    """
    variants = type.to_variants()

    grants_no_grant_option: List[Grant] = []
    grants_with_grant_option: List[Grant] = []

    if acl is not None:
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
    else:
        assert owner is not None
        priv = None
        grantor = owner
        grantee = owner
        grants_no_grant_option.extend(list(variants))

    grants = []
    for grant_option, grant_privileges in (
        (False, grants_no_grant_option),
        (True, grants_with_grant_option),
    ):
        if not grant_privileges:
            continue

        # By putting the grants in a group by itself before iterating over it,
        # non-`expanded` versions will take the whole set as a single group.
        if expanded:
            grant_groups = [[g] for g in grant_privileges]
        else:
            grant_groups = [grant_privileges]

        for grant_group in grant_groups:
            grant = Grant(
                target_role=grantee,
                grants=tuple(sorted(grant_group)),  # type: ignore
                grant_option=grant_option,
            )
            grants.append(grant)

    if priv:
        assert len(grants) > 0

    return grantor, grants


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
