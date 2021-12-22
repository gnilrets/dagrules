import pytest

import dagrules.core
from dagrules.core import RuleSubject

@pytest.fixture
def manifest():
    return {
        'nodes': {
            'model.db.mymodel': {
                'resource_type': 'model',
                'name': 'mymodel',
                'tags': [],
                'depends_on': {
                    'nodes': [
                        'snapshot.db.mysnapshot'
                    ]
                }
            },
            'snapshot.db.mysnapshot': {
                'resource_type': 'snapshot',
                'name': 'mysnapshot',
                'tags': [],
                'depends_on': {
                    'nodes': [
                        'source.db.schema.mysource'
                    ]
                }
            }
        },
        'sources': {
            'source.db.schema.mysource': {
                'name': 'mysource',
                'tags': []
            }
        },
        'child_map': {
            'source.db.schema.mysource': [
                'snapshot.db.mysnapshot'
            ],
            'snapshot.db.mysnapshot': [
                'model.db.mymodel'
            ],
            'model.db.mymodel': []
        },
    }


def test_identify_node_by_name(manifest):
    pass
