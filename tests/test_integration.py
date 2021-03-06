"""
Tests a complete dagrules spec against an example manifest
"""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import os
import json

import yaml

import dagrules


def test_integration():
    # Example dbt manifest that demonstrates the source->snapshot->base->staging->intermediate->dim->fct flow model
    test_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(test_dir, "dagrules.yml"), encoding="utf-8") as rules_file:
        config = yaml.safe_load(rules_file)

    with open(os.path.join(test_dir, "manifest.json"), encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    dagrules.core.validate(config)
    dagrules.core.check(config, manifest)
