from pathlib import Path
from collections import namedtuple
from configkit import ValidationError
from configkit.schema import Schema
import json
import pytest

SchemaInfo = namedtuple("SchemaInfo", ["name", "version"])


def generate_schema_fixture(filename):
    @pytest.fixture
    def fixie():
        with Path(__file__).with_name("schemas").joinpath(filename).open(encoding="utf-8") as fp:
            return json.load(fp)

    return fixie


config_definition = generate_schema_fixture("config-1.0.json")
credentials_definition = generate_schema_fixture("credentials-1.0.json")


@pytest.fixture
def definitions(config_definition, credentials_definition):
    return {defi["$id"]: defi for defi in [config_definition, credentials_definition]}


@pytest.fixture
def mock_schemas(definitions, mocker):
    return [mocker.Mock(definition=defin, id=def_id) for (def_id, defin) in definitions.items()]


@pytest.fixture
def mock_directory(mock_schemas, mocker):
    directory = mocker.Mock(**{
        'schemas.return_value': mock_schemas
    })
    return directory


@pytest.fixture
def valid_config():
    return {
        "keep_alive": False,
        "resources": [
            "sugar",
            {
                "type": "static",
                "name": "spice"
            }
        ]
    }


@pytest.fixture
def valid_credentials():
    return {
        "client_id": "$foo$",
        "secret_key": "!bar!"
    }


@pytest.fixture
def valid_config_with_credentials(valid_config, valid_credentials):
    return {**valid_config, "credentials": valid_credentials}


@pytest.fixture
def invalid_config():
    return {
        "keep_alive": True
    }


@pytest.fixture
def invalid_credentials():
    return {
        "client_id": "$foo!"
    }


@pytest.fixture
def path(request):
    return request.getfixturevalue("{}_path".format(request.param))


@pytest.fixture(params=[
    'valid_config',
    'valid_credentials',
    'valid_config_with_credentials',
    'invalid_config',
    'invalid_credentials'
])
def data(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(params=['config', 'credentials'])
def definition(request):
    return request.getfixturevalue('{}_definition'.format(request.param))


def generate_path_fixture_for(name):
    @pytest.fixture()
    def fixie(request, tmp_path):
        obj = request.getfixturevalue(name)
        config_path = tmp_path.joinpath("fn-{}.json".format(name))
        with config_path.open("w", encoding="utf-8") as fp:
            json.dump(obj, fp)
        return config_path

    return fixie


valid_config_path = generate_path_fixture_for("valid_config")
valid_credentials_path = generate_path_fixture_for("valid_credentials")
valid_config_with_credentials_path = generate_path_fixture_for(
    "valid_config_with_credentials")
invalid_config_path = generate_path_fixture_for("invalid_config")
invalid_credentials_path = generate_path_fixture_for("invalid_credentials")


def generate_empty_path_for_suffix(suffix):
    @pytest.fixture()
    def fixie(tmp_path):
        target = tmp_path.joinpath("config")

        if suffix:
            target = target.with_suffix(suffix)

        with target.open("w"):
            pass
        return target
    return fixie


empty_yaml_path = generate_empty_path_for_suffix(".yaml")
empty_toml_path = generate_empty_path_for_suffix(".toml")
empty_xyz_path = generate_empty_path_for_suffix(".xyz")
empty_nosuffix_path = generate_empty_path_for_suffix("")


@pytest.fixture(params=['yaml', 'toml'])
def empty_path(request):
    return request.getfixturevalue("empty_{}_path".format(request.param))


@pytest.fixture(params=['xyz', 'nosuffix'])
def empty_invalid_suffix_path(request):
    return request.getfixturevalue("empty_{}_path".format(request.param))


def test_raise_import_error_without_known_extras(config_definition, mock_directory, empty_path):
    schema = Schema(config_definition, None, mock_directory)

    with pytest.raises(ImportError, match=r"pip install configkit\[[^\]]+\]"):
        schema.load(str(empty_path))


def test_raise_value_error_with_unknown_suffix(config_definition, mock_directory, empty_invalid_suffix_path):
    schema = Schema(config_definition, None, mock_directory)

    with pytest.raises(ValueError):
        schema.load(str(empty_invalid_suffix_path))


def test_custom_loader_with_unknown_suffix(
        config_definition, mock_directory, empty_invalid_suffix_path,
        valid_config, mocker):
    schema = Schema(config_definition, None, mock_directory)

    loader = mocker.stub()
    loader.return_value = valid_config

    assert schema.load(str(empty_invalid_suffix_path),
                       use=loader) == valid_config
    assert loader.call_count == 1


@pytest.mark.parametrize("data,path,definition", [
    ('valid_config', 'valid_config', 'config'),
    ('valid_config_with_credentials', 'valid_config_with_credentials', 'config'),
    ('valid_credentials', 'valid_credentials', 'credentials')
], indirect=True)
def test_load_valid_config(path, definition, mock_directory, data):
    schema = Schema(definition, None, mock_directory)
    assert schema.load(str(path)) == data


@pytest.mark.parametrize("data,path,definition", [
    ('invalid_config', 'invalid_config', 'config'),
    ('invalid_credentials', 'invalid_credentials', 'credentials')
], indirect=True)
def test_load_invalid_config(path, definition, mock_directory, data):
    schema = Schema(definition, None, mock_directory)
    with pytest.raises(ValidationError):
        schema.load(str(path))
