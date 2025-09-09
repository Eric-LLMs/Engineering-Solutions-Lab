import os
import pytest
import sys
import yaml

from pathlib import Path

__dir__ = Path(__file__).resolve().parent
__base__ = __dir__.parent.parent
__conf__ = __base__.joinpath('conf')

sys.path.append(str(__base__))

def loadDataFromYaml(fname):
    '''
    load data from yaml-format file
    @param fname: filename
    @return data
    '''
    if not os.path.isfile(fname):
        raise FileNotFoundError('{} not found'.format(fname))

    with open(fname, 'rt') as f:
        data = yaml.safe_load(f)

    if data is None: return {}
    else: return data

@pytest.fixture()
def ip(request):
    return '127.0.0.1'

@pytest.fixture()
def port(request):
    config = loadDataFromYaml(str(__conf__.joinpath('service.yml')))

    return config['listen_port']
