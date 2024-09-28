from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Sequence, Union

from sqlalchemy import MetaData
from typing_extensions import Self

from sqlalchemy_declarative_extensions.dialects import postgresql

G = Union[postgresql.DefaultGrantStatement, postgresql.GrantStatement]


@dataclass
class Grants:
    """A collection of grants and the settings for diff/collection.

    Arguments:
        grants: The list of grants
        ignore_unspecified: Defaults to `False`. When `True`, ignore detected grants
            which do not match the set of defined grants.
        ignore_self_grants: Defaults to `True`. When `True`, ignores grants to the
            current user. It's typical in migrations that the a single user performs
            migrations and will have implicitly granted grants on all objects. In this
            scenario, it can be tedious to define those permissions on every object,
            so they are ignored by default.
        only_defined_roles: Defaults to `True`. When `True`, only applies to roles
            specified in the `roles` section.
        default_grants_imply_grants: Defaults to `True`. When `True`, default grants
            also imply the set of expected actual grants. This allows one to specify
            only default grants, and per-object grants will be made to match the
            default set.

    Examples:
        - No grants

        >>> grants = Grants()

        - Some options set

        >>> grants = Grants(ignore_unspecified=True)

        - With some actual grants

        >>> from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant
        >>> grants = Grants().are(DefaultGrant(..., ...), ...)
    """

    grants: list[G] = field(default_factory=list)

    ignore_unspecified: bool = False
    ignore_self_grants: bool = True
    only_defined_roles: bool = True
    default_grants_imply_grants: bool = True

    @classmethod
    def coerce_from_unknown(cls, unknown: None | Iterable[G] | Grants) -> Grants | None:
        if isinstance(unknown, Grants):
            return unknown

        if isinstance(unknown, Iterable):
            return Grants().are(*unknown)

        return None

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["grants"] for m in metadata if m and m.info.get("grants")
        ]

        instance_count = len(instances)
        if instance_count == 0:
            return None

        if instance_count == 1:
            return instances[0]

        if not all(
            x.ignore_unspecified == instances[0].ignore_unspecified
            and x.ignore_self_grants == instances[0].ignore_self_grants
            and x.only_defined_roles == instances[0].only_defined_roles
            and x.default_grants_imply_grants
            == instances[0].default_grants_imply_grants
            for x in instances
        ):
            raise ValueError(
                "All combined `Grants` instances must agree on the set of settings: "
                "ignore_unspecified, ignore_self_grants, only_defined_roles, default_grants_imply_grants"
            )

        grants = [s for instance in instances for s in instance.grants]

        ignore_unspecified = instances[0].ignore_unspecified
        ignore_self_grants = instances[0].ignore_self_grants
        only_defined_roles = instances[0].only_defined_roles
        default_grants_imply_grants = instances[0].default_grants_imply_grants
        return cls(
            grants=grants,
            ignore_unspecified=ignore_unspecified,
            ignore_self_grants=ignore_self_grants,
            only_defined_roles=only_defined_roles,
            default_grants_imply_grants=default_grants_imply_grants,
        )

    def __iter__(self):
        yield from self.grants

    def are(self, *grants: G):
        return replace(self, grants=list(grants))
