import os
import json
import re

# TODO: convert all of this into a pypi package, possibly leveraging pytest to run the assertions

DBT_ROOT = os.getcwd()
if "DBT_ROOT" in os.environ:
    DBT_ROOT = os.environ["DBT_ROOT"]

def parse_dbt_manifest():
    #TODO: change to arg
    with open(os.path.join(DBT_ROOT, "target", "manifest.json")) as mfile:
        dbt_manifest = json.loads(mfile.read())
    return dbt_manifest

def tag_select(tags, select, exclude=None):
    'Returns true if all select are in tags, false if any exclude are in tags'

    if isinstance(tags, str):
        tags = {tags}
    tags = set(tags)

    if isinstance(select, str):
        select = {select}
    select = set(select)

    exclude = exclude or set()
    if isinstance(exclude, str):
        exclude = {exclude}
    exclude = set(exclude)
    return select.issubset(tags) and len(exclude & tags) == 0

def check_node_attribute_matches_pattern(manifest, attrib, pattern, select_tags, exclude_tags=None):
    violations = {
        node: {k: v for k, v in params.items() if k in ['tags', attrib]}
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select=select_tags, exclude=exclude_tags)
        and not re.search(pattern, params[attrib])
    }
    return violations


def test_every_source_has_snapshot(manifest):
    '''
    Every source must have a snapshot
    '''

    sources = {
        source: [ child for child in manifest['child_map'][source] if manifest['nodes'][child]['resource_type'] == 'snapshot' ]
        for source, params in manifest['sources'].items()
    }

    violations = {
        source: children
        for source, children in sources.items() if len(children) == 0
    }

    return violations


def test_snapshot_prefixed_snap(manifest):
    '''
    Snapshot models must be prefixed with snap_
    '''

    return check_node_attribute_matches_pattern(
        manifest,
        attrib='name',
        pattern=r'^snap_',
        select_tags='snapshot'
    )

def test_staging_prefixed_stg(manifest):
    '''
    Non-base staging models must be prefixed with stg_
    '''

    return check_node_attribute_matches_pattern(
        manifest,
        attrib='name',
        pattern=r'^stg_',
        select_tags='staging',
        exclude_tags='base'
    )

def test_base_prefixed_base(manifest):
    '''
    Base models must be prefixed with base_
    '''

    return check_node_attribute_matches_pattern(
        manifest,
        attrib='name',
        pattern=r'^base_',
        select_tags='base',
    )


def test_required_tags(manifest):
    '''
    All models must be tagged with at least one of: snapshot, base, staging, intermediate, core, mart

    '''
    required_tags = {'snapshot', 'base', 'staging', 'intermediate', 'core', 'mart'}

    violations = {
        node: {k: v for k, v in params.items() if k in ['tags', 'resource_type']}
        for node, params in manifest['nodes'].items()
        if params['resource_type'] not in ['test', 'exposure']
        and len(required_tags & set(params['tags'])) == 0
    }
    return violations

def test_snapshot_to_base_cardinality(manifest):
    '''
    All snapshots must have 0 or 1 base model children, nothing else
    '''

    snapshots = {
        node: {
            child: {
                'tags': manifest['nodes'][child]['tags'],
                'is_base': 'base' in manifest['nodes'][child]['tags'],
            }
            for child in manifest['child_map'][node]
            if manifest['nodes'][child]['resource_type'] not in ['test']
        }
        for node, params in manifest['nodes'].items()
        if params['resource_type'] == 'snapshot'
    }

    child_base_counter = {
        node: list(map(lambda child: int(child[1]['is_base']), children.items()))
        for node, children in snapshots.items()
    }

    node_violations = [
        node
        for node, base_counter in child_base_counter.items()
        if not(len(base_counter) == 0 or sum(base_counter) == 1)
    ]

    violations = {
        node: params
        for node, params in snapshots.items()
        if node in node_violations
    }
    return violations

def test_staging_not_depend_on_staging(manifest):
    '''
    Non-base staging models cannot depend on other non-base staging models
    '''

    staging_models = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select='staging', exclude='base')
    }

    violations = {
        node: params
        for node, params in staging_models.items()
        if len(set(params['depends_on']) & set(staging_models.keys())) != 0
    }
    return violations

def test_intermediate_depends(manifest):
    '''
    Intermediate models may only depend on non-base staging, core, mart, or other intermediate models
    '''

    int_models = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select='intermediate')
    }

    allowed_depends = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if (
            tag_select(tags=params['tags'], select='staging', exclude='base')
            or
            tag_select(tags=params['tags'], select='intermediate')
            or
            tag_select(tags=params['tags'], select='mart')
        )
    }

    violations = {
        node: params
        for node, params in int_models.items()
        if (
            not set(params['depends_on']).issubset(set(allowed_depends.keys()))
        )

    }
    return violations


def test_core_models_must_be_tagged(manifest):
    '''
    Core models must be tagged as either dim or fct
    '''

    required_tags = {'dim', 'fct'}

    violations = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
        }
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select='core')
           and len(required_tags & set(params['tags'])) == 0
    }
    return violations



def test_core_dim_only_depends(manifest):
    '''
    Core dimension models should only depend on staging or intermediate models.
    '''

    core_models = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select=['core', 'dim'])
    }

    allowed_depends = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if (
            tag_select(tags=params['tags'], select='staging', exclude='base')
            or
            tag_select(tags=params['tags'], select='intermediate')
        )
    }

    violations = {
        node: params
        for node, params in core_models.items()
        if (
            not set(params['depends_on']).issubset(set(allowed_depends.keys()))
            and
            not tag_select(tags=params['tags'], select='dim_cv')
        )

    }
    return violations


def test_core_fct_only_depends(manifest):
    '''
    Core fact models should only depend on staging, intermediate models, or dimension models.
    '''

    core_models = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if tag_select(tags=params['tags'], select=['core', 'fct'])
    }

    allowed_depends = {
        node: {
            'tags': params['tags'],
            'resource_type': params['resource_type'],
            'depends_on': params['depends_on']['nodes']
        }
        for node, params in manifest['nodes'].items()
        if (
            tag_select(tags=params['tags'], select='staging', exclude='base')
            or
            tag_select(tags=params['tags'], select='intermediate')
            or
            tag_select(tags=params['tags'], select='dim')
        )
    }

    violations = {
        node: params
        for node, params in core_models.items()
        if (
            not set(params['depends_on']).issubset(set(allowed_depends.keys()))
            and
            not tag_select(tags=params['tags'], select='dim_cv')
        )

    }
    return violations


def test_violations(manifest, fun):
    violations = fun(manifest)
    if len(violations) != 0:
        msg = f'{fun.__doc__.strip()}\n\nViolations:\n\n{json.dumps(violations, indent=4)}'
        raise AssertionError(msg)

if __name__ == '__main__':
    manifest = parse_dbt_manifest()

    tests = [
        test_every_source_has_snapshot,
        test_snapshot_prefixed_snap,
        test_staging_prefixed_stg,
        test_base_prefixed_base,
        test_required_tags,
        test_snapshot_to_base_cardinality,
        test_staging_not_depend_on_staging,
        test_intermediate_depends,
        test_core_models_must_be_tagged,
        test_core_dim_only_depends,
        test_core_fct_only_depends,
    ]
    for test in tests:
        test_violations(manifest, test)

    print('All dagrules passed!')
