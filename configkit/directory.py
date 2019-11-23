from . import versions
from . import schema
from . import matchers
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Iterator
import os
import json


class Directory(Mapping):
    def __init__(
        self, path: str, matcher: "matchers.IMatcher" = matchers.version_name_matcher
    ):
        self.path = path
        self.matcher = matcher
        self._cache = None

    def __repr__(self) -> str:
        return "Directory(path={!r})".format(self.path)

    def __len__(self) -> int:
        with self.scan_if_needed():
            return len(self._cache)

    def __iter__(self) -> Iterator[str]:
        with self.scan_if_needed() as cache:
            return (name for name in cache)

    def __getitem__(self, key: str) -> "versions.Versions":
        with self.scan_if_needed() as cache:
            version_list = cache[key]
            return versions.Versions(version_list)

    def values(self) -> Iterator["versions.Versions"]:
        with self.ensure_cache():
            yield from super().values()

    def keys(self) -> Iterator[str]:
        with self.ensure_cache():
            yield from super().keys()

    def find(self) -> Iterator["schema.Schema"]:
        """Iterate over the directory path and yield valid schemas."""
        with self.ensure_cache() as cache:
            for dirpath, dirnames, filenames in os.walk(self.path):
                for filename in filenames:
                    filepath = Path(dirpath, filename)
                    match = self.matcher.check(str(filepath))
                    if match:
                        try:
                            with filepath.open("r", encoding="utf-8") as fp:
                                definition = json.load(fp)
                        except BaseException:
                            raise
                        else:
                            if schema.Schema.check(definition):
                                sch = schema.Schema(definition, match, self)
                                cache.setdefault(sch.name, []).append(sch)
                                yield sch

    def schemas(
        self, version_spec: Optional[str] = None, sort_key=None, reverse=False
    ) -> Iterator["schema.Schema"]:
        seen = set()

        for vers in self.values():
            vers = vers if version_spec is None else vers.filtered(version_spec)
            vers = vers if sort_key is None else vers.sorted(sort_key, reverse)
            for sch in vers:
                if sch not in seen:
                    yield sch
                    seen.add(sch)

    @contextmanager
    def scan_if_needed(self):
        with self.ensure_cache() as cache:
            if not cache:
                for item in self.find():
                    pass
            yield cache

    @contextmanager
    def ensure_cache(self):
        cache = {} if self._cache is None else self._cache
        with self.use_cache(cache):
            yield cache

    @contextmanager
    def use_cache(self, cache=None):
        cache = {} if cache is None else cache
        old_cache = self._cache
        self._cache = cache
        yield
        self._cache = old_cache
