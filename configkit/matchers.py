from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import NamedTuple, Optional, Any
import re


SchemaInfo = NamedTuple(
    "SchemaInfo", [("name", str), ("version", Optional[str])])


class IMatcher(ABC):
    """ABC that checks if a filepath refers to a schema."""

    @abstractmethod
    def check(self, path: str) -> Optional[SchemaInfo]:
        """Return a SchemaInfo if the given path refers to a schema"""


class RegexMatcher(IMatcher):
    """
    A Matcher that uses a regular expression to match filenames.

    >>> sm = RegexMatcher(r"(?:(?P<version>[^/\\\\]+?)(?:/|\\\\))?(?P<name>[^/\\\\]+?).json")
    >>> sm.check("foo/bar.json")
    SchemaInfo(name='bar', version='foo')
    >>> sm.check("foo/bar/baz.json")
    SchemaInfo(name='baz', version='bar')
    >>> sm = RegexMatcher(r"(?P<name>[^/\\\\]+?)(?:(?:/|\\\\)(?P<version>[^/\\\\]+?))?.json$")
    >>> sm.check("foo/bar.json")
    SchemaInfo(name='foo', version='bar')
    >>> sm.check("foo.json")
    SchemaInfo(name='foo', version=None)

    """

    def __init__(self, pattern: str):
        self.pattern = pattern

    def check(self, path: str) -> Optional[SchemaInfo]:
        match = self._regexp.search(path)
        if match:
            d = match.groupdict()
            return SchemaInfo(d["name"], d.get("version"))

    @property
    def pattern(self) -> str:
        return self._regexp.pattern

    @pattern.setter
    def pattern(self, pattern: str):
        regexp = re.compile(pattern)

        if "name" not in regexp.groupindex:
            raise ValueError(
                "pattern must have a capture group called 'name'.")

        self._regexp = regexp


version_name_matcher = RegexMatcher(
    r"(?:(?P<version>[^/\\]+?)(?:/|\\))?(?P<name>[^/\\]+?).json")
name_version_matcher = RegexMatcher(
    r"(?P<name>[^/\\]+?)(?:(?:/|\\)(?P<version>[^/\\]+?))?.json$")

__all__ = ['SchemaInfo', 'IMatcher', 'RegexMatcher',
           'version_name_matcher', 'name_version_matcher']


if __name__ == "__main__":
    import doctest
    doctest.testmod()
