import pytest
import shutil
from pathlib import PurePath, Path
from configkit import SchemaDirectory
from configkit.matchers import (
    version_name_matcher as vnm,
    name_version_matcher as nvm,
    RegexMatcher,
)
from configkit.versions import Versions
from configkit.schema import Schema


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "schemas")


@pytest.fixture
def same_level_matcher(path):
    shutil.copytree(str(PurePath(__file__).with_name("schemas")), path)
    return RegexMatcher(r"(?P<name>[^/\\]+?)-(?P<version>[^/\\]+?).json$")


@pytest.fixture
def version_name_matcher(path):
    tmp_path = Path(path)
    subs = ["0.1", "0.2", "1.0"]
    root = PurePath(__file__).with_name("schemas")

    tmp_path.mkdir()

    for sub in subs:
        (tmp_path / sub).mkdir()

    shutil.copyfile(
        str(root / "config-0.1.json"), str(tmp_path / "0.1" / "config.json")
    )
    shutil.copyfile(
        str(root / "credentials-0.1.json"), str(tmp_path / "0.1" / "credentials.json")
    )
    shutil.copyfile(
        str(root / "config-1.0.json"), str(tmp_path / "1.0" / "config.json")
    )
    shutil.copyfile(
        str(root / "credentials-1.0.json"), str(tmp_path / "1.0" / "credentials.json")
    )
    shutil.copyfile(
        str(root / "config-0.2.json"), str(tmp_path / "0.2" / "config.json")
    )
    return vnm


@pytest.fixture
def name_version_matcher(path):
    tmp_path = Path(path)
    subs = ["credentials", "config"]
    root = PurePath(__file__).with_name("schemas")

    tmp_path.mkdir()

    for sub in subs:
        (tmp_path / sub).mkdir()

    shutil.copyfile(
        str(root / "config-0.1.json"), str(tmp_path / "config" / "0.1.json")
    )
    shutil.copyfile(
        str(root / "credentials-0.1.json"), str(tmp_path / "credentials" / "0.1.json")
    )
    shutil.copyfile(
        str(root / "config-1.0.json"), str(tmp_path / "config" / "1.0.json")
    )
    shutil.copyfile(
        str(root / "credentials-1.0.json"), str(tmp_path / "credentials" / "1.0.json")
    )
    shutil.copyfile(
        str(root / "config-0.2.json"), str(tmp_path / "config" / "0.2.json")
    )
    return nvm  # lol


@pytest.fixture(
    params=["same_level_matcher", "version_name_matcher", "name_version_matcher"]
)
def matcher(request):
    return request.getfixturevalue(request.param)


def test_length(path, matcher):
    print(matcher)
    assert len(SchemaDirectory(path, matcher)) == 2


def test_keys(path, matcher):
    directory = SchemaDirectory(path, matcher)
    assert set(directory.keys()) == set(["config", "credentials"])
    assert set(directory) == set(["config", "credentials"])


def test_every_schema_found(path, matcher):
    directory = SchemaDirectory(path, matcher)

    assert {sch.id for sch in directory["config"]} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/{}/config.json".format(v)
        for v in ["0.1", "0.2", "1.0"]
    }

    assert {sch.id for sch in directory["credentials"]} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/{}/credentials.json".format(
            v
        )
        for v in ["0.1", "1.0"]
    }


def test_values_are_versions(path, matcher):
    directory = SchemaDirectory(path, matcher)

    for name in directory:
        assert isinstance(directory[name], Versions)

    for item in directory.values():
        assert isinstance(item, Versions)


def test_iter_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    for item in directory:
        pass

    assert directory.find.call_count == 1


def test_lookup_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    directory["config"]

    assert directory.find.call_count == 1


def test_len_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    len(directory)

    assert directory.find.call_count == 1


def test_membership_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    "config" in directory

    assert directory.find.call_count == 1


def test_keys_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    list(directory.keys())

    assert directory.find.call_count == 1


def test_values_scans_once(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    list(directory.values())

    assert directory.find.call_count == 1


def test_scans_once_with_use_cache(path, matcher, mocker):
    directory = SchemaDirectory(path, matcher)
    mocker.spy(directory, "find")

    with directory.use_cache():
        assert directory.find.call_count == 0

        list(directory)
        assert directory.find.call_count == 1

        list(directory.values())
        assert directory.find.call_count == 1

        "credentials" in directory
        assert directory.find.call_count == 1

        directory["credentials"]
        assert directory.find.call_count == 1

    assert directory.find.call_count == 1


def test_use_cache_gives_correct_results(path, matcher):
    directory = SchemaDirectory(path, matcher)
    with directory.use_cache():
        assert len(directory) == 2
        assert set(directory) == set(["credentials", "config"])

        assert {sch.id for sch in directory["config"]} == {
            "https://github.com/mr-rodgers/configkit/test/schemas/0.1/config.json",
            "https://github.com/mr-rodgers/configkit/test/schemas/0.2/config.json",
            "https://github.com/mr-rodgers/configkit/test/schemas/1.0/config.json",
        }

        assert {sch.id for sch in directory["credentials"]} == {
            "https://github.com/mr-rodgers/configkit/test/schemas/0.1/credentials.json",
            "https://github.com/mr-rodgers/configkit/test/schemas/1.0/credentials.json",
        }


def test_schemas_iterates_schema_instances(path, matcher):
    directory = SchemaDirectory(path, matcher)

    specs = [None, "==0.2", "~=1.0", "<1"]

    for spec in specs:
        for sch in directory.schemas(spec):
            assert isinstance(sch, Schema)


def test_schemas_iterates_correct_schema_ids(path, matcher):
    directory = SchemaDirectory(path, matcher)

    assert {s.id for s in directory.schemas()} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/0.1/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/0.2/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/1.0/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/0.1/credentials.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/1.0/credentials.json",
    }

    assert {s.id for s in directory.schemas("==0.2")} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/0.2/config.json"
    }

    assert {s.id for s in directory.schemas(">=1.0")} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/1.0/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/1.0/credentials.json",
    }

    assert {s.id for s in directory.schemas("<1")} == {
        "https://github.com/mr-rodgers/configkit/test/schemas/0.1/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/0.2/config.json",
        "https://github.com/mr-rodgers/configkit/test/schemas/0.1/credentials.json",
    }
