import pytest
from configkit import version_sort_key
from configkit.versions import Versions
from collections import namedtuple

MockSchema = namedtuple("MockSchema", ["version"])


@pytest.fixture
def basic():
    """Basic Version instance."""
    schemas = [MockSchema("5.3.2"), MockSchema("0.9"), MockSchema(
        "1.9"), MockSchema("11.0"), MockSchema(None)]
    return Versions(schemas)


@pytest.fixture(params=[
    [MockSchema("0.1"), MockSchema(None), MockSchema("11.2.1")],
    [],
    [MockSchema("1.1"), MockSchema("0.9.4")]
])
def schemas(request):
    return request.param


def test_schema_len(schemas):
    versions = Versions(schemas)
    assert len(schemas) == len(versions)


def test_matched_order(schemas):
    versions = Versions(schemas)
    assert list(schemas) == list(versions)


def test_idx_lookup(schemas):
    versions = Versions(schemas)
    for i, schema in enumerate(schemas):
        assert schemas[i] == versions[i]


def test_lookup_by_version_spec(basic):
    assert basic.version('>8').version == '11.0'
    assert basic.version('==0.9').version == '0.9'
    assert basic.version('==1.0', match_unversioned=False) is None
    assert basic.version('>19').version is None
    assert basic.version('<6.1').version == '5.3.2'
    assert basic.version('>4.1').version == '5.3.2'


def test_lookup_by_version_spec_sorted(basic):
    assert basic.version('<6.1', sort_key=version_sort_key).version == '0.9'
    assert basic.version('>4.1', sort_key=version_sort_key).version == '5.3.2'
    assert basic.version('>4.1', sort_key=version_sort_key,
                         reverse=True).version is None
    assert basic.version('>4.1', sort_key=version_sort_key,
                         reverse=True, match_unversioned=False).version == '11.0'


def test_lookup_newest(basic):
    assert basic.newest().version is None
    assert basic.newest(match_unversioned=False).version == '11.0'
    assert basic.newest('<11', match_unversioned=False).version == '5.3.2'
    assert basic.newest('<0.1', match_unversioned=False) is None


def test_lookup_oldest(basic):
    assert basic.oldest().version == '0.9'
    assert basic.oldest('>1.0').version == '1.9'
    assert basic.oldest('>1000').version is None
    assert basic.oldest('>1000', match_unversioned=False) is None
