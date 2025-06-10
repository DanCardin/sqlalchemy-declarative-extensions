from __future__ import annotations

from typing import Any


class MigrateOp:
    def reverse(self) -> MigrateOp:
        raise NotImplementedError()

    def to_diff_tuple(self) -> tuple[Any, ...]:
        raise NotImplementedError()


class ExecuteOp(MigrateOp):
    def to_sql(self) -> list[str]:
        raise NotImplementedError()

    def to_diff_tuple(self) -> tuple[Any, ...]:
        return "execute", *self.to_sql()
