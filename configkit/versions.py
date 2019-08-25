from collections.abc import Sequence
from typing import Any, Callable, List, Optional

from packaging.specifiers import SpecifierSet
from packaging.version import parse

from . import schema

SortKey = Callable[['schema.Schema'], Any]


class Versions(Sequence):
    def __init__(self, versions: List['schema.Schema']):
        self.versions = versions

    def __len__(self) -> int:
        return len(self.versions)

    def __getitem__(self, idx: int) -> 'schema.Schema':
        return self.versions[idx]

    def sorted(self, key: SortKey, reverse=False) -> 'Versions':
        return Versions(sorted(self, key=key, reverse=reverse))

    def filtered(self, specifier: str, match_unversioned=True) -> 'Versions':
        acceptable_versions = SpecifierSet(specifier)

        def matches_requirements(sch):
            if not sch.version:
                return match_unversioned
            else:
                version = parse(sch.version)
                return version in acceptable_versions
        return Versions([sch for sch in self.versions if matches_requirements(sch)])

    def version(self, specifier: str, sort_key: Optional[SortKey] = None, reverse=False, match_unversioned=True) -> Optional['schema.Schema']:
        """Return the first schema that matches the version spec

        :param specifier: a :pep:`440` version specifier
        :param sort_key: if given, the versions will be sorted
                         accordingly before returning the first
                         matching schema
        :param reverse: Return the last matching schema instead
        :param match_unversioned: unless true, unversioned schemas
                                  will not count as matches
        """
        versions = self.filtered(specifier, match_unversioned)
        try:
            return next(iter(versions if sort_key is None else versions.sorted(sort_key, reverse)))
        except StopIteration:
            return None

    def newest(self, specifier: str = ">=0", match_unversioned=True) -> Optional['schema.Schema']:
        return self.version(specifier, version_sort_key, reverse=True, match_unversioned=match_unversioned)

    def oldest(self, specifier: str = ">=0", match_unversioned=True) -> Optional['schema.Schema']:
        return self.version(specifier, version_sort_key, match_unversioned=match_unversioned)


def version_sort_key(sch: 'schema.Schema') -> Any:
    return parse('9999999.9999999' if sch.version is None else sch.version)
