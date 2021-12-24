import pytest

import dagrules.core
from dagrules.core import (
    rule_subjects,
    rule_match_name,
    rule_have_tags_any,
    rule_have_child_relationship,
    rule_have_parent_relationship,
    RuleError,
)

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

def test_have_child_relationship_pass():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a'],
            'snapshot.snap_b': ['model.base_b'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    try:
        rule_have_child_relationship(subjects, cardinality='one_to_one', required_tags='base')
    except RuleError as err:
        assert False, str(err)

def test_have_parent_relationship_pass():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot', 'tags': ['snapshot']},
            'snapshot.snap_b': {'resource_type': 'snapshot', 'tags': ['snapshot']},
            'model.base_a': {
                'resource_type': 'model',
                'tags': ['base'],
                'depends_on': {'nodes': ['snapshot.snap_a']}
            },
            'model.base_b': {
                'resource_type': 'model',
                'tags': ['base'],
                'depends_on': {'nodes': ['snapshot.snap_b']}
            },
        },
    }
    subjects = rule_subjects(manifest, tags='base')

    try:
        rule_have_parent_relationship(subjects, cardinality='one_to_one', required_tags='snapshot')
    except RuleError as err:
        assert False, str(err)

def test_have_child_relationship_fail_cardinality():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a', 'model.base_b'],
            'snapshot.snap_b': ['model.base_b'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    with pytest.raises(RuleError):
        rule_have_child_relationship(subjects, cardinality='one_to_one', required_tags='base')

def test_have_child_relationship_fail_required_relationship():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    with pytest.raises(RuleError):
        rule_have_child_relationship(subjects, cardinality='one_to_one', required_tags='base')

def test_have_child_relationship_pass_not_required_relationship():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    try:
        rule_have_child_relationship(subjects, cardinality='one_to_one', required=False, required_tags='base')
    except RuleError as err:
        assert False, str(err)

def test_have_child_relationship_fail_required_tagas():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['not-base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a'],
            'snapshot.snap_b': ['model.base_b'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    with pytest.raises(RuleError):
        rule_have_child_relationship(subjects, cardinality='one_to_one', required_tags='base')

def test_have_child_relationship_selected_tags_pass():
    manifest = {
        'nodes': {
            'snapshot.snap_a': {'resource_type': 'snapshot'},
            'snapshot.snap_b': {'resource_type': 'snapshot'},
            'model.base_a': {'resource_type': 'model', 'tags': ['base']},
            'model.base_b': {'resource_type': 'model', 'tags': ['not-base']},
        },
        'child_map': {
            'snapshot.snap_a': ['model.base_a'],
            'snapshot.snap_b': ['model.base_b'],
        }
    }
    subjects = rule_subjects(manifest, node_type='snapshot')

    try:
        rule_have_child_relationship(subjects, required=False, select_tags='base', required_tags='base')
    except RuleError as err:
        assert False, str(err)
