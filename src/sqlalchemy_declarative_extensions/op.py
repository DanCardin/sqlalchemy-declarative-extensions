from dataclasses import dataclass


@dataclass
class Op:
    def reverse(self):
        raise NotImplementedError()

    def to_sql(self) -> list[str]:
        raise NotImplementedError()

    def to_diff_tuple(self) -> tuple[str, str]:
        return ("execute", self.to_sql())
