"""
Tests related to dagrules musts
"""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import pytest

from dagrules.core import (
    rule_subjects,
    rule_match_name,
    rule_have_tags_any,
    rule_have_relationship,
    RuleError,
    ParserAllowedValueError,
)


def test_match_name_pass():
    manifest = {
        "nodes": {
            "model.stg_a": {"resource_type": "model", "name": "stg_a"},
            "model.stg_b": {"resource_type": "model", "name": "stg_b"},
        }
    }
    subjects = rule_subjects(manifest)
    try:
        rule_match_name(subjects, "/stg_.*/")
    except RuleError as err:
        assert False, str(err)


def test_match_name_fail():
    manifest = {
        "nodes": {
            "model.stg_a": {"resource_type": "model", "name": "stg_a"},
            "model.base_b": {"resource_type": "model", "name": "base_b"},
        }
    }
    subjects = rule_subjects(manifest)
    with pytest.raises(RuleError):
        rule_match_name(subjects, "/stg_.*/")


def test_have_tags_any_pass():
    manifest = {
        "nodes": {
            "model.base_a": {"resource_type": "model", "tags": ["base", "staging"]},
            "model.stg_b": {"resource_type": "model", "tags": ["staging"]},
        }
    }
    subjects = rule_subjects(manifest)
    try:
        rule_have_tags_any(subjects, ["base", "staging"])
    except RuleError as err:
        assert False, str(err)


def test_have_tags_any_fail():
    manifest = {
        "nodes": {
            "model.base_a": {"resource_type": "model", "tags": ["base", "staging"]},
            "model.stg_b": {"resource_type": "model", "tags": ["staging"]},
        }
    }
    subjects = rule_subjects(manifest)
    with pytest.raises(RuleError):
        rule_have_tags_any(subjects, {"include": "staging", "exclude": "base"})


def test_have_child_relationship_pass():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
            "snapshot.snap_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    try:
        rule_have_relationship(subjects, "child", cardinality="one_to_one", require_tags_any="base")
    except RuleError as err:
        assert False, str(err)


def test_have_parent_relationship_pass():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot", "tags": ["snapshot"]},
            "snapshot.snap_b": {"resource_type": "snapshot", "tags": ["snapshot"]},
            "model.base_a": {
                "resource_type": "model",
                "tags": ["base"],
                "depends_on": {"nodes": ["snapshot.snap_a"]},
            },
            "model.base_b": {
                "resource_type": "model",
                "tags": ["base"],
                "depends_on": {"nodes": ["snapshot.snap_b"]},
            },
        },
    }
    subjects = rule_subjects(manifest, tags="base")

    try:
        rule_have_relationship(
            subjects, "parent", cardinality="one_to_one", require_tags_any="snapshot"
        )
    except RuleError as err:
        assert False, str(err)


def test_have_child_relationship_fail_kwargs():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
            "snapshot.snap_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    with pytest.raises(ParserAllowedValueError):
        rule_have_relationship(
            subjects, "child", cardinality="one_to_one", require_tags_any="base", monkeys="not here"
        )


def test_have_child_relationship_fail_cardinality():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a", "model.base_b"],
            "snapshot.snap_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    with pytest.raises(RuleError):
        rule_have_relationship(subjects, "child", cardinality="one_to_one", require_tags_any="base")


def test_have_child_relationship_fail_required_relationship():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    with pytest.raises(RuleError):
        rule_have_relationship(subjects, "child", cardinality="one_to_one", require_tags_any="base")


def test_have_child_relationship_pass_not_required_relationship():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    try:
        rule_have_relationship(
            subjects, "child", cardinality="one_to_one", required=False, require_tags_any="base"
        )
    except RuleError as err:
        assert False, str(err)


def test_have_child_relationship_fail_required_tagas():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["not-base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
            "snapshot.snap_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    with pytest.raises(RuleError):
        rule_have_relationship(subjects, "child", cardinality="one_to_one", require_tags_any="base")


def test_have_child_relationship_selected_tags_pass():
    manifest = {
        "nodes": {
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "snapshot.snap_b": {"resource_type": "snapshot"},
            "model.base_a": {"resource_type": "model", "tags": ["base"]},
            "model.base_b": {"resource_type": "model", "tags": ["not-base"]},
        },
        "child_map": {
            "snapshot.snap_a": ["model.base_a"],
            "snapshot.snap_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="snapshot")

    try:
        rule_have_relationship(
            subjects, "child", required=False, select_tags_any="base", require_tags_any="base"
        )
    except RuleError as err:
        assert False, str(err)


def test_have_child_relationship_select_node_type_pass():
    manifest = {
        "nodes": {
            "source.src_a": {"resource_type": "source"},
            "source.src_b": {"resource_type": "source"},
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "model.base_b": {"resource_type": "model"},
        },
        "child_map": {
            "source.src_a": ["snapshot.snap_a"],
            "source.src_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="source")

    try:
        rule_have_relationship(
            subjects,
            "child",
            required=False,
            select_node_type="snapshot",
            require_node_type="snapshot",
        )
    except RuleError as err:
        assert False, str(err)


def test_have_child_relationship_require_node_type_fail():
    manifest = {
        "nodes": {
            "source.src_a": {"resource_type": "source"},
            "source.src_b": {"resource_type": "source"},
            "snapshot.snap_a": {"resource_type": "snapshot"},
            "model.base_b": {"resource_type": "model"},
        },
        "child_map": {
            "source.src_a": ["snapshot.snap_a"],
            "source.src_b": ["model.base_b"],
        },
    }
    subjects = rule_subjects(manifest, node_type="source")

    with pytest.raises(RuleError):
        rule_have_relationship(subjects, "child", required=False, require_node_type="snapshot")
