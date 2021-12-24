import pytest

import dagrules.core
from dagrules.core import rule_subjects, rule_match_name, rule_have_tags_any, RuleError

def test_match_name_pass():
    manifest = {
        'nodes': {
            'model.stg_a': {'resource_type': 'model', 'name': 'stg_a'},
            'model.stg_b': {'resource_type': 'model', 'name': 'stg_b'},
        }
    }
    subjects = rule_subjects(manifest)
    try:
        rule_match_name(subjects, '/stg_.*/')
    except RuleError as err:
        assert False, str(err)


def test_match_name_fail():
    manifest = {
        'nodes': {
            'model.stg_a': {'resource_type': 'model', 'name': 'stg_a'},
            'model.base_b': {'resource_type': 'model', 'name': 'base_b'},
        }
    }
    subjects = rule_subjects(manifest)
    with pytest.raises(RuleError):
        rule_match_name(subjects, '/stg_.*/')


def test_have_tags_any_pass():
    manifest = {
        'nodes': {
            'model.base_a': {'resource_type': 'model', 'tags': ['base', 'staging']},
            'model.stg_b': {'resource_type': 'model', 'tags': ['staging']},
        }
    }
    subjects = rule_subjects(manifest)
    try:
        rule_have_tags_any(subjects, ['base', 'staging'])
    except RuleError as err:
        assert False, str(err)

def test_have_tags_any_fail():
    manifest = {
        'nodes': {
            'model.base_a': {'resource_type': 'model', 'tags': ['base', 'staging']},
            'model.stg_b': {'resource_type': 'model', 'tags': ['staging']},
        }
    }
    subjects = rule_subjects(manifest)
    with pytest.raises(RuleError):
        rule_have_tags_any(subjects, {'include': 'staging', 'exclude': 'base'})
