import os
import argparse
import json

import yaml

DBT_ROOT = os.getcwd()
if "DBT_ROOT" in os.environ:
    DBT_ROOT = os.environ["DBT_ROOT"]
DAGRULES_YAML = os.path.join(DBT_ROOT, "dagrules.yml")

def parse_args():
    parser = argparse.ArgumentParser(description="dagrules cli")

    parser.add_argument(
        "--validate",
        dest='validate',
        const=True,
        nargs='?',
        default=False,
        help="Runs dagrules define in dagrules.yml"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.validate:
        validate(args)

def read_rules():
    'Read yaml rules file'

    with open(DAGRULES_YAML) as f:
        rules = yaml.safe_load(f)
    return rules

def validate(args):
    print(json.dumps(read_rules(), indent=4))
