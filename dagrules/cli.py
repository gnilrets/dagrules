"""
The dagrules cli
"""

import os
import argparse
import json

import yaml

import dagrules.core

DBT_ROOT = os.getcwd()
if "DBT_ROOT" in os.environ:
    DBT_ROOT = os.environ["DBT_ROOT"]
DAGRULES_YAML = os.path.join(DBT_ROOT, "dagrules.yml")


def _parse_args():
    parser = argparse.ArgumentParser(description="dagrules cli")

    parser.add_argument(
        "--check",
        dest="check",
        const=True,
        nargs="?",
        default=False,
        help="Runs dagrules define in dagrules.yml",
    )

    return parser.parse_args()


def main():
    "Entry point for the command line interface"
    args = _parse_args()

    config = _read_config()
    manifest = _read_manifest()

    if args.check:
        dagrules.core.validate(config)
        dagrules.core.check(config, manifest)


def _read_config():
    "Read yaml rules file"

    with open(DAGRULES_YAML, encoding="utf-8") as rules_file:
        config = yaml.safe_load(rules_file)
    return config


def _read_manifest():
    "Read the dbt manifest.json file"

    with open(os.path.join(DBT_ROOT, "target", "manifest.json"), encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    return manifest
