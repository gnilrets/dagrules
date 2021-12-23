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
            'model.stg_b': {'resource_type': 'model', 'name': 'stg_b'},
        }
    }
    subject = RuleSubject(manifest)
    with pytest.raises(RuleError):
        dagrules.core.rule_match_name(subject, '/base_.*/')
