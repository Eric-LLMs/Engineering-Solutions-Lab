import pytest

from .common import loadClientConfig, initializeClient

def pytest_addoption(parser):
    config = loadClientConfig()

    parser.addoption('--ip', help='service ip', default='localhost')
    parser.addoption('--port', help='service port', type=int, default=config['interfaces']['grpc']['args']['listen_port'])

@pytest.fixture
def ip(request):
    return request.config.getoption('--ip')

@pytest.fixture
def port(request):
    return request.config.getoption('--port')
