import enum
from typing import Iterable, List, Type, TypeVar, Union

FromStringsSelf = TypeVar("FromStringsSelf", bound="FromStrings")


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
        else:
            return string
