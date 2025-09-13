import logging
import traceback

from .base_interface import BaseInterface
from .grpc_interface import GrpcInterface, GrpcService
from framework import FrameworkException

def loadInterface(c: BaseInterface, name: str=None, **kwargs) -> BaseInterface:
    '''
    载入服务接口
    @param c: 接口类
    @param name: 接口名
    @return 载入的接口实例，如果失败，则返回 None
    '''
    instance = c(name)
    try:
        instance.loadFromConfig(**kwargs)
        logging.info('loaded interface {}'.format(instance))

        return instance
    except Exception as ex:
        logging.error('failed to load interface {}'.format(instance))

        if not isinstance(ex, FrameworkException):
            logging.error(traceback.format_exc())

        return None
