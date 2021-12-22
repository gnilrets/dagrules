class ParseError(BaseException): pass


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

class RuleSubject:
    PARSER = {
        'allowed_args': {'type', 'tags'},
        'node_types': {'model', 'snapshot', 'source'}
    }

    def __init__(self, manifest, node_type='model', tags=None):
        self.manifest = manifest
        self.node_type = node_type
        self.tags = tags

    @classmethod
    def parse(cls, opts, rule_name=''):
        unknown_args = set(opts.keys()) - __class__.PARSER['allowed_args']
        if len(unknown_args) > 0:
            raise ParseError(f'Unexpected subject arguments "{unknown_args}" for rule "{rule_name}"')

        if not isinstance(opts, dict):
            raise ParseError(f'Expecting subject arguments for rule "{rule_name}"')

        node_type = opts.get('type', 'model')
        if node_type not in __class__.PARSER["node_types"]:
            raise ParseError(f'Unknown subject type "{node_type}" for rule "{rule_name}".  Expecting one of {__class__.PARSER["node_types"]}')

        return RuleSubject(node_type=node_type, tags=opts.get('tags'))

    def selected(self):
        flat_nodes = {**self.manifest.get('sources', {}), **self.manifest['nodes']}

        selected_nodes = {
            node: {**params, **{'children': self.manifest.get('child_map', {}).get(node, [])}}
            for node, params in flat_nodes.items()
            if params['resource_type'] == self.node_type and match_tags_any(params.get('tags', []), self.tags)
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

class RuleMust:
    PARSER = {
        'allowed_args': {'match-name', 'have-tag', 'relationship', 'relationship-required', 'related-tags'}
    }

    def __init__(self):
        pass

    @classmethod
    def parse(cls, opts, rule_name=''):
        unknown_args = set(opts.keys()) - __class__.PARSER['allowed_args']
        if len(unknown_args) > 0:
            raise ParseError(f'Unexpected must arguments "{unknown_args}" for rule "{rule_name}"')

        if not isinstance(opts, dict):
            raise ParseError(f'Expecting must arguments for rule "{rule_name}"')
