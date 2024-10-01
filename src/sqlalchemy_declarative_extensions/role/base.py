from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generator, Iterable, Sequence

from sqlalchemy import MetaData
from typing_extensions import Self

from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.role import generic


@dataclass
class Roles:
    roles: Sequence[postgresql.Role | generic.Role] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_roles: list[str] = field(default_factory=list)

    @classmethod
    def coerce_from_unknown(
        cls,
        unknown: None | Iterable[postgresql.Role | generic.Role | str] | Roles,
    ) -> Roles | None:
        if isinstance(unknown, Roles):
            return unknown

        if isinstance(unknown, Iterable):
            return Roles().are(*unknown)

        return None

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["roles"] for m in metadata if m and m.info.get("roles")
        ]

        instance_count = len(instances)
        if instance_count == 0:
            return None

        if instance_count == 1:
            return instances[0]

        if not all(
            x.ignore_unspecified == instances[0].ignore_unspecified for x in instances
        ):
            raise ValueError(
                "All combined `Roles` instances must agree on the set of settings: ignore_unspecified"
            )

        roles = tuple(s for instance in instances for s in instance.roles)
        ignore_roles = [s for instance in instances for s in instance.ignore_roles]

        ignore_unspecified = instances[0].ignore_unspecified
        return cls(
            roles=roles,
            ignore_unspecified=ignore_unspecified,
            ignore_roles=ignore_roles,
        )

    def __iter__(self) -> Generator[postgresql.Role | generic.Role, None, None]:
        yield from self.roles

    def are(self, *roles: postgresql.Role | generic.Role | str):
        return replace(
            self,
            roles=[generic.Role.coerce_from_unknown(role) for role in roles],
        )
