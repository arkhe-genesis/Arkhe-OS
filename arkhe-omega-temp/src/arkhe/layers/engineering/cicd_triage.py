# src/arkhe/layers/engineering/cicd_triage.py
def generate_pipeline():
    pipeline = {
        'name': 'Arkhe CI',
        'on': ['push', 'pull_request'],
        'jobs': {
            'lint': {'runs-on': 'ubuntu-latest', 'steps': ['checkout', 'run: tox -e lint']},
            'test': {'runs-on': 'ubuntu-latest', 'steps': ['checkout', 'run: tox']},
            'audit': {'runs-on': 'ubuntu-latest', 'steps': ['checkout', 'run: pip-audit']},
            'supply-chain': {'runs-on': 'ubuntu-latest', 'steps': ['checkout', 'run: arkp audit --supply-chain']}
        }
    }
    return pipeline
