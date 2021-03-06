"""
Tests related to selecting subject nodes
"""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

from dagrules.core import rule_subjects


def test_identify_model_by_tag():
    manifest = {
        "nodes": {
            "model.a": {"resource_type": "model", "tags": ["staging"]},
            "model.b": {"resource_type": "model", "tags": ["not-staging"]},
            "model.c": {"resource_type": "model", "tags": ["staging"]},
        }
    }

    subjects = rule_subjects(manifest, tags=["staging"])

    actual = sorted(list(subjects.keys()))
    expected = sorted(["model.a", "model.c"])
    assert actual == expected


def test_identify_model_by_tag_complex():
    manifest = {
        "nodes": {
            "model.a": {"resource_type": "model", "tags": ["base", "staging"]},
            "model.b": {"resource_type": "model", "tags": ["staging"]},
            "model.c": {"resource_type": "model", "tags": ["staging"]},
        }
    }
    subjects = rule_subjects(manifest, tags={"include": "staging", "exclude": "base"})

    actual = sorted(list(subjects.keys()))
    expected = sorted(["model.b", "model.c"])
    assert actual == expected


def test_identify_source():
    manifest = {
        "sources": {"source.a": {"resource_type": "source"}},
        "nodes": {"model.b": {"resource_type": "model"}},
    }

    subjects = rule_subjects(manifest, node_type="source")

    actual = sorted(list(subjects.keys()))
    expected = sorted(["source.a"])
    assert actual == expected


def test_identify_snapshot():
    manifest = {
        "nodes": {
            "snapshot.a": {"resource_type": "snapshot"},
            "model.b": {"resource_type": "model"},
        },
    }

    subjects = rule_subjects(manifest, node_type="snapshot")

    actual = sorted(list(subjects.keys()))
    expected = sorted(["snapshot.a"])
    assert actual == expected


def test_selected_chilren_properties():
    manifest = {
        "nodes": {
            "model.a": {"resource_type": "model", "tags": ["base", "staging"]},
            "model.b": {"resource_type": "model", "tags": ["staging"]},
            "model.c": {"resource_type": "model", "tags": ["staging"]},
        },
        "child_map": {
            "model.a": [
                "model.b",
                "model.c",
            ],
            "model.b": [],
            "model.c": [],
        },
    }

    subjects = rule_subjects(manifest, tags=["base"])

    children = subjects["model.a"]["child_params"]
    assert len(children) == 2

    actual = {child: params.get("tags") for child, params in children.items()}
    expected = {
        "model.b": ["staging"],
        "model.c": ["staging"],
    }
    assert actual == expected


def test_selected_parent_properties():
    manifest = {
        "nodes": {
            "model.a": {
                "resource_type": "model",
                "tags": ["base", "staging"],
                "depends_on": {"nodes": []},
            },
            "model.b": {
                "resource_type": "model",
                "tags": ["base", "staging"],
                "depends_on": {"nodes": []},
            },
            "model.c": {
                "resource_type": "model",
                "tags": ["staging"],
                "depends_on": {"nodes": ["model.a", "model.b"]},
            },
        }
    }

    subjects = rule_subjects(manifest, tags={"include": "staging", "exclude": "base"})

    parents = subjects["model.c"]["parent_params"]
    assert len(parents) == 2

    actual = {parent: params.get("tags") for parent, params in parents.items()}
    expected = {
        "model.a": ["base", "staging"],
        "model.b": ["base", "staging"],
    }
    assert actual == expected
