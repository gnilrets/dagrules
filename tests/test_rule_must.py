import pytest

import dagrules.core
from dagrules.core import RuleSubject, RuleMust, RuleError

def test_match_name_pass():
    manifest = {
        'nodes': {
            'model.stg_a': {'resource_type': 'model', 'name': 'stg_a'},
            'model.stg_b': {'resource_type': 'model', 'name': 'stg_b'},
        }
    }
    subject = RuleSubject(manifest)
    try:
        dagrules.core.rule_match_name(subject, '/stg_.*/')
    except RuleError as err:
        assert False, str(err)


def test_match_name_fail():
    manifest = {
        'nodes': {
            'model.stg_a': {'resource_type': 'model', 'name': 'stg_a'},
            'model.base_b': {'resource_type': 'model', 'name': 'base_b'},
        }
    }
    subject = RuleSubject(manifest)
    with pytest.raises(RuleError):
        dagrules.core.rule_match_name(subject, '/stg_.*/')


def test_have_tags_any_pass():
    manifest = {
        'nodes': {
            'model.base_a': {'resource_type': 'model', 'tags': ['base', 'staging']},
            'model.stg_b': {'resource_type': 'model', 'tags': ['staging']},
        }
    }
    subject = RuleSubject(manifest)
    try:
        dagrules.core.rule_have_tags_any(subject, ['base', 'staging'])
    except RuleError as err:
        assert False, str(err)

def test_have_tags_any_fail():
    manifest = {
        'nodes': {
            'model.base_a': {'resource_type': 'model', 'tags': ['base', 'staging']},
            'model.stg_b': {'resource_type': 'model', 'tags': ['staging']},
        }
    }
    subject = RuleSubject(manifest)
    with pytest.raises(RuleError):
        dagrules.core.rule_have_tags_any(subject, {'include': 'staging', 'exclude': 'base'})
