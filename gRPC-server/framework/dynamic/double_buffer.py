import logging
import threading
from typing import Union, Any

from .dynamic_data import DynamicData
from framework import FrameworkException, ErrCode, loadClass

class DoubleBuffer():
    '''
    双缓冲，用于支持数据的reload
    '''
    def __init__(self, name: str, _class: Union[str, Any], **kwargs):
        '''
        初始化
        @param name: 缓冲区名
        @param _class: 实现类名/类
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.buffer = [ None ] * 2
        self.buffer_idx = 0 # 缓冲区切换索引
        self.reload_mutex = threading.RLock() # reload 锁

        if isinstance(_class, str):
            self.impl = loadClass(_class)
        else:
            self.impl = _class
        if self.impl is None:
            self.logger.error('failed to load double buffer class {}'.format(_class))
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

        self.kwargs = kwargs
        if not self.reload():
            self.logger.error('failed to load buffer {}'.format(self.name))
            raise FrameworkException(errcode=ErrCode.FAILED_TO_LOAD_FILE)
        self.version = 1    # 数据版本号

    def __expr__(self) -> str:
        if self.name:
            return '{}:{}'.format(self.__class__.__name__, self.name)
        else:
            return self.__class__.__name__

    def __getattr__(self, attr: str) -> Any:
        '''
        该函数用于简化动态词典调用
        '''
        data = self.get()

        return getattr(data, attr)

    def get(self) -> DynamicData:
        '''
        获取当前生效数据
        '''
        return self.buffer[self.buffer_idx % 2]

    def reload(self) -> bool:
        '''
        重载数据
        '''
        with self.reload_mutex:
            oldIdx = self.buffer_idx % 2
            newIdx = (self.buffer_idx + 1) % 2

            if self.buffer[newIdx] is not None:
                self.buffer[newIdx].release() # 释放数据
                self.buffer[newIdx] = None

            d = self.impl(self.name)
            if not d.load(**self.kwargs):
                return False

            self.buffer[newIdx] = d
            self.buffer_idx += 1

        return True
