import logging
import traceback

from .base_layer import BaseLayer, LayerMode, ParallelLayer
from framework import FrameworkException

def loadLayer(c: BaseLayer, **kwargs) -> ParallelLayer:
    '''
    载入服务接口
    @param config: 配置数据
    @return 载入的并发层实例，如果失败，则返回 None
    '''
    try:
        instance = ParallelLayer(c, **kwargs)

        logging.info('loaded parallel layer {}'.format(c.__name__))

        return instance
    except Exception as ex:
        logging.error('failed to load parallel layer {}'.format(c.__name__))

        if not isinstance(ex, FrameworkException):
            logging.error(traceback.format_exc())

        return None
