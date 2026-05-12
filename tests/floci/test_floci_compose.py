import yaml

def test_floci_in_compose():
    with open('config/docker/docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)
    assert 'floci' in compose['services']
    assert compose['services']['floci']['image'] == 'floci/floci:latest'
    assert '4566:4566' in compose['services']['floci']['ports']
