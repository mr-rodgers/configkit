from . import matchers, directory
from collections import namedtuple
from jsonschema import Draft7Validator as Validator, RefResolver
from pathlib import Path
from typing import Any, Optional
import json

FakeModule = namedtuple("fakemodule", ["load", "safe_load"])


def make_loader(fmt):
    def load(fp):
        raise ImportError(
            "In order to use {0!r}, you must install the extra dependencies. e.g.: `pip install configkit[{0}]`.".format(
                fmt
            )
        )

    return load


try:
    import yaml
except BaseException:
    yaml = FakeModule(make_loader("yaml"), make_loader("yaml"))

try:
    import toml
except BaseException:
    toml = FakeModule(make_loader("toml"), None)


class Schema:
    __slots__ = ("definition", "info", "directory", "formats")

    @staticmethod
    def check(definition):
        try:
            Validator.check_schema(definition)
        except BaseException:
            return False
        else:
            return True

    def __init__(
        self,
        definition: Any,
        info: "matchers.SchemaInfo",
        directory: "directory.Directory",
    ):
        self.definition = definition
        self.info = info
        self.directory = directory
        self.formats = {"json": json.load, "yaml": yaml.safe_load, "toml": toml.load}

    def __hash__(self):
        return hash((self.id,))

    def load(self, filename: str, use=None, encoding="utf-8"):
        path = Path(filename)

        if use is not None:
            load = use
        else:
            if path.suffix[1:] not in self.formats:
                print(path.suffix[1:])
                raise ValueError(
                    "Don't know how to load this file extension: {!r}".format(
                        path.suffix
                    )
                )
            else:
                load = self.formats[path.suffix[1:]]

        with path.open(encoding=encoding) as fp:
            instance = load(fp)

        resolver = RefResolver(
            self.id,
            self.definition,
            {sch.id: sch.definition for sch in self.directory.schemas()},
        )
        validator = Validator(self.definition, resolver=resolver)
        validator.validate(instance)

        return instance

    @property
    def id(self) -> Optional[str]:
        return self.definition.get("$id")

    @property
    def name(self) -> str:
        return self.info.name

    @property
    def version(self) -> Optional[str]:
        return self.info.version
