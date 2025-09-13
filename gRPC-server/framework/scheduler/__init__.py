import logging
import traceback

from .scheduler import Scheduler, RemoteServer
from .random_scheduler import RandomScheduler
from framework import FrameworkException, loadClass
from typing import Union

def loadScheduler(c: Union[Scheduler, str], name: str=None, **kwargs) -> Scheduler:
    '''
    根据配置数据创建调度器实例
    @param c: 调度器类
    @param name: 调度器名字
    @return 调度器实例，如果失败，则返回 None
    '''
    if isinstance(c, str):
        c = loadClass(c)
    if c is None:
        return None

    try:
        instance = c(name, **kwargs)
        logging.info('loaded scheduler {}'.format(instance))

        return instance
    except Exception as ex:
        logging.error('failed to load scheduler {}'.format(c))

        if not isinstance(ex, FrameworkException):
            logging.error(traceback.format_exc())

        return None
