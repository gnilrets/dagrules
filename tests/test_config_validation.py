"""
Tests related to validating the dagrules config file
"""
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name


import pytest

from dagrules.core import (
    validate_root,
    validate_rule_name,
    validate_rule,
    validate_rule_subject,
    validate_rule_must,
    ParseError,
    ParserRequiredValueError,
    ParserAllowedValueError,
)


def test_validate_root_pass():
    dagrules_yaml = {"version": "0", "rules": []}

    try:
        validate_root(dagrules_yaml)
    except ParseError as err:
        assert False, str(err)


def test_validate_root_fail_no_version():
    dagrules_yaml = {"rules": []}

    with pytest.raises(ParserRequiredValueError):
        validate_root(dagrules_yaml)


def test_validate_root_fail_no_rules():
    dagrules_yaml = {"version": "0"}

    with pytest.raises(ParserRequiredValueError):
        validate_root(dagrules_yaml)


def test_validate_root_fail_unknown_keys():
    dagrules_yaml = {"version": "0", "bruh": "sup", "rules": []}

    with pytest.raises(ParserAllowedValueError):
        validate_root(dagrules_yaml)


def test_rule_pass():
    rule = {"name": "bob", "subject": {}, "must": {}}

    try:
        validate_rule("bob", rule)
    except ParseError as err:
        assert False, str(err)


def test_validate_rule_no_name_fail():
    rule = {"subject": {}, "must": {}}

    with pytest.raises(ParserRequiredValueError):
        validate_rule_name(3, rule)


def test_validate_rule_fail_missing_keys():
    rule = {"name": "bob", "subject": {}}

    with pytest.raises(ParserRequiredValueError):
        validate_rule("bob", rule)


def test_validate_rule_fail_unknown_keys():
    rule = {"name": "bob", "subject": {}, "must": {}, "bruh": "sup"}

    with pytest.raises(ParserAllowedValueError):
        validate_rule("bob", rule)


def test_validate_rule_subject_pass():
    subject = {"type": "snapshot"}

    try:
        validate_rule_subject("bob", subject)
    except ParseError as err:
        assert False, str(err)


def test_validate_rule_subject_fail_unknown_keys():
    subject = {"bruh": "sup"}

    with pytest.raises(ParserAllowedValueError):
        validate_rule_subject("bob", subject)


def test_validate_rule_must_pass():
    must = {"have-tags-any": ["a", "b"]}

    try:
        validate_rule_must("bob", must)
    except ParseError as err:
        assert False, str(err)


def test_validate_rule_must_fail_unknown_keys():
    must = {"bruh": "sup"}

    with pytest.raises(ParserAllowedValueError):
        validate_rule_must("bob", must)
