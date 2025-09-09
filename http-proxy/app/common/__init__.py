import logging
import yaml
from pathlib import Path

# logging.yml
LOGGING_FILENAME = Path('conf/logging.yml')
# log 目录
LOG_DIRNAME = Path('log')

def initLogger():
    '''
    初始化logging
    '''
    try:
        if LOG_DIRNAME.exists():
            if not LOG_DIRNAME.is_dir():
                logging.critical('{} is not a valid directory'.format(LOG_DIRNAME))
        else:
            LOG_DIRNAME.mkdir(parents=True)

        with LOGGING_FILENAME.open('rt') as f:
            data = yaml.safe_load(f)

        logging.config.dictConfig(data)
    except Exception as ex:
        logging.fatal('failed to load logging config {}: {}'.format(LOGGING_FILENAME, ex))
        raise ex

from .common import loadModuleClass, AppRtnCode, AppException
from .performance import PerformanceTimer

import logging

# 函数计时器修饰器
def timer_api(f):
    def timer_function(
        *args,
        **kwargs
    ):
        timer = PerformanceTimer()
        with timer:
            out = f(*args, **kwargs)

        logging.debug('{} takes {} ms'.format(f.__name__, timer.read_millisecond()))

        return out

    return timer_function
