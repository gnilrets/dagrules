import pytest

import dagrules.core
from dagrules.core import match_tags, match_tags_any

@pytest.fixture
def tags():
    return [
        'aa',
        'bb',
        'cc'
    ]

def test_tags_include_single(tags):
    assert match_tags(tags, 'bb') is True

def test_tags_not_include_single(tags):
    assert match_tags(tags, 'xx') is False

def test_tags_include_multiple(tags):
    assert match_tags(tags, ['aa', 'cc']) is True

def test_tags_not_include_multiple(tags):
    assert match_tags(tags, ['aa', 'xx']) is False

def test_tags_exclude_single(tags):
    assert match_tags(tags, 'aa', exclude='bb') is False

def test_tags_not_exclude_single(tags):
    assert match_tags(tags, 'aa', exclude='xx') is True

def test_tags_exclude_multiple(tags):
    assert match_tags(tags, 'aa', exclude=['bb', 'xx']) is False

def test_tags_not_exclude_multiple(tags):
    assert match_tags(tags, 'aa', exclude=['xx', 'yy']) is True



def test_tags_any_single_string(tags):
    assert match_tags_any(tags, 'aa') is True

def test_tags_not_any_single_string(tags):
    assert match_tags_any(tags, 'xx') is False

def test_tags_any_single_dict(tags):
    assert match_tags_any(tags, {'include': 'aa'}) is True

def test_tags_any_single_dict_exclude(tags):
    assert match_tags_any(tags, {'include': 'aa', 'exclude': 'bb'}) is False

def test_tags_any_multiple_strings(tags):
    assert match_tags_any(tags, ['bb', 'xx']) is True

def test_tags_not_any_multiple_strings(tags):
    assert match_tags_any(tags, ['xx', 'yy']) is False

def test_tags_any_multiple_mixed(tags):
    assert match_tags_any(tags, ['xx', {'include': ['aa'], 'exclude': 'xx'}]) is True

def test_tags_not_any_multiple_mixed(tags):
    assert match_tags_any(tags, ['xx', {'include': ['aa', 'yy'], 'exclude': 'xx'}]) is False
