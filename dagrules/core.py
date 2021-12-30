import re

class ParseError(BaseException): pass
class ParserAllowedKeyError(ParseError): pass
class ParserRequiredKeyError(ParseError): pass
class ParserArgumentError(ParseError): pass


class RuleError(BaseException): pass


def match_tags(tags, include=None, exclude=None):
    'Returns true if ALL include are in tags, false if ANY exclude are in tags'

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
        return {'include': matcher}
    if isinstance(matcher, dict):
        return {'include': matcher.get('include'), 'exclude': matcher.get('exclude')}
    return None


def match_tags_any(tags, matchers=None):
    if matchers is None:
        return True

    if isinstance(tags, str):
        tags = {tags}
    tags = set(tags)

    if isinstance(matchers, str) or isinstance(matchers, dict):
        matchers = [_sanitize_tag_matcher(matchers)]
    else:
        matchers = [_sanitize_tag_matcher(matcher) for matcher in matchers]

    for matcher in matchers:
        if match_tags(tags, **matcher):
            return True
    return False

def validate(dagrules_yaml):
    validate_root(dagrules_yaml)
    for idx, rule in enumerate(dagrules_yaml['rules']):
        validate_rule_name(idx, rule)
        validate_rule(rule['name'], rule)
        # validate_subject(rule['name', rule['subject'])
        # validate_must(rule['name'], rule['must'])

def validate_keys(keys, allowed_keys=None, required_keys=None):
    keys = set(keys)
    allowed_keys = set() if allowed_keys is None else set(allowed_keys)
    required_keys = set() if required_keys is None else set(required_keys)

    unknown_keys = keys - allowed_keys
    if len(unknown_keys) > 0 and len(allowed_keys) > 0:
        raise ParserAllowedKeyError(str(unknown_keys))

    if not required_keys.issubset(keys):
        raise ParserRequiredKeyError(str(required_keys - keys))


def validate_root(config):
    try:
        validate_keys(
            keys=config.keys(),
            allowed_keys={'version', 'rules'},
            required_keys={'version', 'rules'},
        )
    except ParserAllowedKeyError as err:
        raise ParserAllowedKeyError(f'Unknown dagrules parameters: {err}')
    except ParserRequiredKeyError as err:
        raise ParserRequiredKeyError(f'Required dagrules parameters not found: {err}')

def validate_rule_name(rule_idx, config):
    if 'name' not in config.keys():
        raise ParserRequiredKeyError(f'No name defined for rule at index {rule_idx}')

def validate_rule(name, config):
    try:
        validate_keys(
            keys=config.keys(),
            allowed_keys={'name', 'subject', 'must'},
            required_keys={'name', 'subject', 'must'},
        )
    except ParserAllowedKeyError as err:
        raise ParserAllowedKeyError(f'Unknown parameters for rule "{name}": {err}')
    except ParserRequiredKeyError as err:
        raise ParserRequiredKeyError(f'Required parameters not found for rule "{name}": {err}')

def validate_rule_subject(rule_name, config):
    try:
        validate_keys(
            keys=config.keys(),
            allowed_keys={'type', 'tags'},
            required_keys={},
        )
    except ParserAllowedKeyError as err:
        raise ParserAllowedKeyError(f'Unknown subject parameters for rule "{rule_name}": {err}')
    except ParserRequiredKeyError as err:
        raise ParserRequiredKeyError(f'Required subject parameters not found for rule "{rule_name}": {err}')

# TODO: specifics of subjects
# TODO: musts


class Rule:
    PARSER = {
        'allowed_args': {'name', 'subject', 'must', 'must-not'}
    }

    def __init__(self, name, subject, must):
        self.name = name
        self.subject = subject
        self.must = must

    @classmethod
    def parse(cls, opts):
        unknown_args = set(opts.keys()) - __class__.PARSER['allowed_args']
        if len(unknown_args) > 0:
            raise ParseError(f'Unexpected rule arguments "{unknown_args}" for rule "{rule_name}"')

        if 'name' not in opts:
            raise ParseError(f'No name defined for rule: {opts}')
        name = opts['name']

        if 'subject' not in opts:
            raise ParseError(f'No subject defined for rule: {name}')
        subject = RuleSubject.parse(opts['subject'], rule_name=name)

        if not ('must' in opts or 'must-not' in opts):
            raise ParseError(f'Rule "{name}" does not specify a "must" or "must-not" condition')
        must = 'must parser'

        return Rule(name, subject, must)

#TODO: do something with this
def parse_subject(opts, rule_name=''):
    unknown_args = set(opts.keys()) - __class__.PARSER['allowed_args']
    if len(unknown_args) > 0:
        raise ParseError(f'Unexpected subject arguments "{unknown_args}" for rule "{rule_name}"')

    if not isinstance(opts, dict):
        raise ParseError(f'Expecting subject arguments for rule "{rule_name}"')

    node_type = opts.get('type', 'model')
    if node_type not in __class__.PARSER["node_types"]:
        raise ParseError(f'Unknown subject type "{node_type}" for rule "{rule_name}".  Expecting one of {__class__.PARSER["node_types"]}')



def rule_subjects(manifest, node_type='model', tags=None):
    flat_nodes = {**manifest.get('sources', {}), **manifest['nodes']}

    selected_nodes = {
        node: {**params, **{'children': manifest.get('child_map', {}).get(node, [])}}
        for node, params in flat_nodes.items()
        if params['resource_type'] == node_type and match_tags_any(params.get('tags', []), tags)
    }

    for node, params in selected_nodes.items():
        selected_nodes[node]['child_params'] = {
            child: flat_nodes[child]
            for child in selected_nodes[node]['children']
        }

        selected_nodes[node]['parent_params'] = {
            parent: flat_nodes[parent]
            for parent in selected_nodes[node].get('depends_on', {}).get('nodes', [])
        }

    return selected_nodes


# TODO: do something with this
def parse_must(opts, rule_name=''):
    allowed_args={'match-name', 'have-tag', 'relationship', 'relationship-required', 'related-tags'}
    unknown_args = set(opts.keys()) - __class__.PARSER['allowed_args']
    if len(unknown_args) > 0:
        raise ParseError(f'Unexpected must arguments "{unknown_args}" for rule "{rule_name}"')

    if not isinstance(opts, dict):
        raise ParseError(f'Expecting must arguments for rule "{rule_name}"')

def rule_match_name(subjects, match_name):
    is_regex_match = re.fullmatch('/.*/', match_name) is not None
    if is_regex_match:
        match_name_regex = re.fullmatch('/(.*)/', match_name).group(1)
        has_match = lambda name: re.fullmatch(match_name_regex, name) is not None
    else:
        raise Exception("I don't know how to handle anything other that regex matchers")

    for node, params in subjects.items():
        if not has_match(params['name']):
            raise RuleError(f"For node \"{node}\", \"{params['name']}\" does not match pattern {match_name}")
    return True


def rule_have_tags_any(subjects, tags):
    for node, params in subjects.items():
        if not match_tags_any(params['tags'], tags):
            raise RuleError(f"For node \"{node}\", tags {params['tags']} do not match expected tags {tags}")
    return True

def rule_have_child_relationship(subjects, cardinality='one_to_many', required=True, select_tags=None, required_tags=None):
    return rule_have_relationship(
        subjects,
        relationship='child',
        cardinality=cardinality,
        required=required,
        select_tags=select_tags,
        required_tags=required_tags
    )

def rule_have_parent_relationship(subjects, cardinality='one_to_many', required=True, select_tags=None, required_tags=None):
    return rule_have_relationship(
        subjects,
        relationship='parent',
        cardinality=cardinality,
        required=required,
        select_tags=select_tags,
        required_tags=required_tags
    )

def rule_have_relationship(subjects, relationship=None, cardinality='one_to_many', required=True, select_tags=None, required_tags=None):
    for node, params in subjects.items():
        selected_deps = {
            dep: dep_params
            for dep, dep_params in params[f'{relationship}_params'].items()
            if match_tags_any(dep_params['tags'], select_tags)
        }

        n_deps = len(selected_deps)
        if required and n_deps == 0:
            raise RuleError(f'{relationship} relationship required, not found for node "{node}"')
        if cardinality == 'one_to_one' and n_deps > 1:
            raise RuleError(f'Expecting only one {relationship}, found {n_deps} for node "{node}"')
        for dep, dep_params in selected_deps.items():
            if not match_tags_any(dep_params['tags'], required_tags):
                raise RuleError(
                    f'Expecting all {relationship} relations of "{node}" to have tags {required_tags}, '
                    f'however {relationship} "{dep}" had tags {dep_params["tags"]}'
                )
