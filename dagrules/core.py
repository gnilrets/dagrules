"""
Core dagrules functionality.
"""

import re

from colorama import Fore, Style


class ParseError(BaseException):
    "Indicates a dagrules.yml parsing error"


class ParserAllowedValueError(ParseError):
    "Indicates when a non-allowed value is found in a dagrules.yml config file"


class ParserRequiredValueError(ParseError):
    "Indicates when a required value is not found in a dagrules.yml config file"


class RuleError(BaseException):
    "Indicates that a specified dagrules rule was violated"


def match_tags(tags, include=None, exclude=None):
    """
    Returns true if ALL include are in tags, false if ANY exclude are in tags

    Args:
        tags (str, list): List of tags to be matched/checked
        include (str, list): List of tags that *must* all be in `tags`
        exclude (str, list): List of tags that *must not* be in `tags`
    """

    # Special case - return true if emmpty
    if include is None:
        return True

    if isinstance(tags, str):
        tags = {tags}
    tags = set(tags)

    if isinstance(include, str):
        include = {include}
    include = set(include)

    exclude = exclude or set()
    if isinstance(exclude, str):
        exclude = {exclude}
    exclude = set(exclude)
    return include.issubset(tags) and len(exclude & tags) == 0


def _sanitize_tag_matcher(matcher):
    if isinstance(matcher, str):
        return {"include": matcher}
    if isinstance(matcher, dict):
        return {"include": matcher.get("include"), "exclude": matcher.get("exclude")}
    return None


def match_tags_any(tags, matchers=None):
    """
    Loops through a (possible) list of tags to match and returns true if any match
    the given list.

    Args:
        tags (str, list): list of tags to be matched/checked
        matchers (str, list, dict): List of tags that may match `tags`

    Examples:
        Matching a simple list of tags::
            match_tags_any(['a', 'b'], ['b', 'x', 'y']) # => True
            match_tags_any(['a', 'b'], ['x', 'y']) # => False

        Matching more complex include/exclude logic
            match_tags_any(['a', 'b'], {'include': 'a', 'exclude': 'b'} # => False
            match_tags_any(['a', 'b', 'c'], [{'include': 'a', 'exclude': 'b'}, 'c'] # => True ('c' matches)

    """

    if matchers is None:
        return True

    if isinstance(tags, str):
        tags = {tags}
    tags = set(tags)

    if isinstance(matchers, (str, dict)):
        matchers = [_sanitize_tag_matcher(matchers)]
    else:
        matchers = [_sanitize_tag_matcher(matcher) for matcher in matchers]

    for matcher in matchers:
        if match_tags(tags, **matcher):
            return True
    return False


def validate(config):
    "Validates the dagrules.yml configuration files conforms to specs"

    validate_root(config)
    for idx, rule in enumerate(config["rules"]):
        validate_rule_name(idx, rule)
        validate_rule(rule["name"], rule)
        if "subject" in rule:
            validate_rule_subject(rule["name"], rule["subject"])
        validate_rule_must(rule["name"], rule["must"])


def validate_values(values, allowed_values=None, required_values=None):
    """
    Checks a list of `values` against valid values.

    * Raises an error if any `values` are not in `allowed_values` (unless `allowed_values is None`)
    * Raises an error if any `required_values` are not in `values`  (unless `required_values is None`)
    """

    values = set(values)
    allowed_values = set() if allowed_values is None else set(allowed_values)
    required_values = set() if required_values is None else set(required_values)

    unknown_values = values - allowed_values
    if len(unknown_values) > 0 and len(allowed_values) > 0:
        raise ParserAllowedValueError(str(unknown_values))

    if not required_values.issubset(values):
        raise ParserRequiredValueError(str(required_values - values))


def validate_root(config):
    "Validates the root dagrules.yml configuration file is valid."

    try:
        validate_values(
            values=config.keys(),
            allowed_values={"version", "rules"},
            required_values={"version", "rules"},
        )
    except ParserAllowedValueError as err:
        raise ParserAllowedValueError(f"Unknown dagrules parameters: {err}") from err
    except ParserRequiredValueError as err:
        raise ParserRequiredValueError(f"Required dagrules parameters not found: {err}") from err


def validate_rule_name(rule_idx, config):
    "Validates that each rule has a name"

    if "name" not in config.keys():
        raise ParserRequiredValueError(f"No name defined for rule at index {rule_idx}")


def validate_rule(name, config):
    "Validates the dagrules.yml configuration for rules."

    try:
        validate_values(
            values=config.keys(),
            allowed_values={"name", "subject", "must"},
            required_values={"name", "must"},
        )
    except ParserAllowedValueError as err:
        raise ParserAllowedValueError(f'Unknown parameters for rule "{name}": {err}') from err
    except ParserRequiredValueError as err:
        raise ParserRequiredValueError(
            f'Required parameters not found for rule "{name}": {err}'
        ) from err


def validate_rule_subject(rule_name, config):
    "Validates the dagrules.yml configuration for subjects."

    try:
        validate_values(
            values=config.keys(),
            allowed_values={"type", "tags"},
            required_values={},
        )
    except ParserAllowedValueError as err:
        raise ParserAllowedValueError(
            f'Unknown subject parameters for rule "{rule_name}": {err}'
        ) from err
    except ParserRequiredValueError as err:
        raise ParserRequiredValueError(
            f'Required subject parameters not found for rule "{rule_name}": {err}'
        ) from err


def validate_rule_must(rule_name, config):
    "Validates the dagrules.yml configuration for musts."

    try:
        validate_values(
            values=config.keys(),
            allowed_values={
                "have-child-relationship",
                "have-parent-relationship",
                "match-name",
                "have-tags-any",
            },
            required_values={},
        )
    except ParserAllowedValueError as err:
        raise ParserAllowedValueError(
            f'Unknown must parameters for rule "{rule_name}": {err}'
        ) from err
    except ParserRequiredValueError as err:
        raise ParserRequiredValueError(
            f'Required must parameters not found for rule "{rule_name}": {err}'
        ) from err


def check(config, manifest):
    "Checks whether any dagrules rules specified are violated"

    version = config["version"]
    if str(version) != "1":
        raise ParserAllowedValueError("dagrules.yml config version must be '1'")

    has_error = False
    for rule in config["rules"]:
        subject_config = rule.get("subject", {})
        subjects = rule_subjects(
            manifest, node_type=subject_config.get("type", "model"), tags=subject_config.get("tags")
        )

        try:
            print(f'Checking rule {rule["name"]}', end=" ... ")
            check_rule(rule, subjects)
            print(Fore.GREEN + "PASSED" + Style.RESET_ALL)

        except RuleError as err:
            print(Fore.RED + "FAILED")
            print(err)
            print(Style.RESET_ALL)
            has_error = True

    if has_error:
        raise RuleError("There were dagrule rule errors, see log")


def check_rule(rule, subjects):
    "Checks whether a specific rule is violated."

    if "match-name" in rule["must"]:
        rule_match_name(subjects, rule["must"]["match-name"])

    if "have-tags-any" in rule["must"]:
        rule_have_tags_any(subjects, rule["must"]["have-tags-any"])

    if "have-child-relationship" in rule["must"]:
        kwargs = {
            k.replace("-", "_"): v for k, v in rule["must"]["have-child-relationship"].items()
        }
        rule_have_relationship(subjects, "child", **kwargs)

    if "have-parent-relationship" in rule["must"]:
        kwargs = {
            k.replace("-", "_"): v for k, v in rule["must"]["have-parent-relationship"].items()
        }
        rule_have_relationship(subjects, "parent", **kwargs)


def rule_subjects(manifest, node_type="model", tags=None):
    "Finds all of the dbt nodes specified by a dagrules subject."

    flat_nodes = {**manifest.get("sources", {}), **manifest["nodes"]}

    selected_nodes = {
        node: {**params, **{"children": manifest.get("child_map", {}).get(node, [])}}
        for node, params in flat_nodes.items()
        if params["resource_type"] == node_type and match_tags_any(params.get("tags", []), tags)
    }

    for node, params in selected_nodes.items():
        selected_nodes[node]["child_params"] = {
            child: flat_nodes[child] for child in selected_nodes[node]["children"]
        }

        selected_nodes[node]["parent_params"] = {
            parent: flat_nodes[parent]
            for parent in selected_nodes[node].get("depends_on", {}).get("nodes", [])
        }

    return selected_nodes


def rule_match_name(subjects, match_name):
    "Checks whether subjects match the name required"

    is_regex_match = re.fullmatch("/.*/", match_name) is not None
    if is_regex_match:
        match_name_regex = re.fullmatch("/(.*)/", match_name).group(1)
        has_match = lambda name: re.fullmatch(match_name_regex, name) is not None
    else:
        raise RuleError("I don't know how to handle anything other that regex matchers")

    for node, params in subjects.items():
        if not has_match(params["name"]):
            raise RuleError(
                f"For node \"{node}\", \"{params['name']}\" does not match pattern {match_name}"
            )
    return True


def rule_have_tags_any(subjects, tags):
    "Checks whehter subjects have the tags specified"

    for node, params in subjects.items():
        if not match_tags_any(params["tags"], tags):
            raise RuleError(
                f"For node \"{node}\", tags {params['tags']} do not match expected tags {tags}"
            )
    return True


def rule_have_relationship(subjects, relationship, **kwargs):  # pylint: disable=too-many-locals
    "Checks whether subjects have the specified relationships"

    unknown_kwargs = set(kwargs.keys()) - {
        "cardinality",
        "required",
        "select_node_type",
        "require_node_type",
        "select_tags_any",
        "require_tags_any",
    }
    unknown_kwargs = {v.replace("_", "-") for v in unknown_kwargs}
    if len(unknown_kwargs) > 0:
        raise ParserAllowedValueError(
            f"Unknown argument to have-{relationship}-relationship: {unknown_kwargs}"
        )

    cardinality = kwargs.get("cardinality", "one_to_many")
    required = kwargs.get("required", True)
    select_node_type = kwargs.get("select_node_type", None)
    require_node_type = kwargs.get("require_node_type", None)
    select_tags_any = kwargs.get("select_tags_any", None)
    require_tags_any = kwargs.get("require_tags_any", None)

    for node, params in subjects.items():
        selected_deps = {
            dep: dep_params
            for dep, dep_params in params[f"{relationship}_params"].items()
            if match_tags_any(dep_params.get("tags"), select_tags_any)
            and (select_node_type is None or select_node_type == dep_params["resource_type"])
        }

        n_deps = len(selected_deps)
        if required and n_deps == 0:
            raise RuleError(f'{relationship} relationship required, not found for node "{node}"')
        if cardinality == "one_to_one" and n_deps > 1:
            raise RuleError(f'Expecting only one {relationship}, found {n_deps} for node "{node}"')
        for dep, dep_params in selected_deps.items():
            if not match_tags_any(dep_params.get("tags"), require_tags_any):
                raise RuleError(
                    f'Expecting all {relationship} relations of "{node}" to have tags {require_tags_any}, '
                    f'however {relationship} "{dep}" had tags {dep_params["tags"]}'
                )
            if require_node_type is not None and dep_params["resource_type"] != require_node_type:
                raise RuleError(
                    f'Expecting all {relationship} relations of "{node}" to be of node type "{require_node_type}", '
                    f'however {relationship} "{dep}" had type "{dep_params["resource_type"]}"'
                )
