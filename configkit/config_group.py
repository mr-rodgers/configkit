from collections.abc import Mapping, Set, Mapping
from pathlib import Path

from jsonpath_rw import parse as parse_jp

from . import matchers
from . import directory
from . import versions


class ConfigGroup(Mapping, SubbingMixin):
    def __init__(
            self, schema_path, config_path, matcher=matchers.version_name_matcher,
            version_spec='>=0', default=None
    ):
        self.directory = directory.SchemaDirectory(schema_path, matcher)
        self.configs = {}
        self._version_spec = version_spec
        self._default = default
        self._config_path = config_path

        self.refresh(paths, version_spec)

    def refresh(self, config_path=None, version_spec=None, default=None):
        config_path = Path(
            self._config_path if config_path is None else config_path)
        version_spec = self._version_spec if version_spec is None else version_spec
        default = self._default if default is None else default

        self.configs = {}
        filenames = ({p.with_suffix('').name: p for p in config_path.iterdir(
        ) if p.is_file()} if config_path.is_dir() else {})

        for schema_name, versions in self.directory.items():
            schema = versions.newest(version_spec)
            cfg = schema.load(
                filenames[schema_name]
            ) if schema_name in filenames else {}
            self.configs[schema_name] = cfg

        if default is not None:
            for key, val in self.configs[default].items():
                self.configs[key] = val

    @property
    def wrapped(self):
        return self.configs


class SubbingMixin:
    subst_regex = re.compile(r"\${{(.+?)}}", re.M)

    @classmethod
    def substitute_value(cls, val, configs):
        if isinstance(val, str):
            seen_paths = set()

            cur_val = val
            match = cls.subst_regex.search(cur_val)

            while match:
                start_index, end_index = match.span(0)

                p = match.group(1)

                if p in seen_paths:
                    raise ValueError(f"Cyclic substitution on: {p}")

                jsonpath = parse_jp(f"$.{p}")
                if "Slice(" in jsonpath and (start_index > m.pos or end_index < len(cur_val)):
                    raise ValueError(f"Cannot substitute slice unless substitution occupies the entire value: {cur_val}")

                submatches = [
                    jmatch.value for jmatch in jsonpath.find(configs)]
                # hacky, but can't find an api to do this properly
                repl = submatches if "Slice(" in repr(
                    jsonpath) else submatches[0]

                cur_val = f"{cur_val[:start_index]}{repl}{cur_val[end_index:]}" if isinstance(repl, str) else SubbingSequence(repl, configs)
                match = cls.subst_regex.search(
                    cur_val) if isinstance(cur_val, str) else None

            return cur_val

        else if isinstance(val, Mapping):
            return SubbingMapping(val, configs)

        else if isinstance(val, Sequence):
            return SubbingSequence(val, configs)

        else if isinstance(val, Set):
            return SubbingSet(val, configs)

        else:
            return val

    def __init__(self, wrapped, configs):
        self.wrapped = wrapped
        self.configs = configs

    def __len__(self):
        return len(self.wrapped)

    def __getitem__(self, key):
        return self.substitute_value(self.wrapped[key], self.configs)

    def __iter__(self):
        return iter(self.wrapped)


class SubbingSet(Set, SubbingMixin):
    def __iter__(self):
        for item in self.wrapped:
            yield self.substitute_value(item, self.configs)


class SubbingMapping(Mapping, SubbingMixin):
    pass


class SubbingSequence(Mapping, SubbingMixin):
    pass
