import enum
import functools
from typing import Iterable, List, Type, TypeVar, Union

FromStringsSelf = TypeVar("FromStringsSelf", bound="FromStrings")


@functools.total_ordering
class FromStrings(enum.Enum):
    @classmethod
    def from_strings(
        cls: Type[FromStringsSelf], strings: Iterable[Union[str, FromStringsSelf]]
    ) -> List[FromStringsSelf]:
        return [cls.from_string(string) for string in strings]

    @classmethod
    def from_string(
        cls: Type[FromStringsSelf], string: Union[str, FromStringsSelf]
    ) -> FromStringsSelf:
        if isinstance(string, str):
            normalized_str = string.upper()
            return cls(normalized_str)
        return string

    def __lt__(self, other):
        return self.value < other.value
